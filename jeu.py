"""Ce module contient la définition de la classe qui encapsule toutes les composantes
du jeu de Paxman.
"""

import json
import pathlib
from datetime import datetime

import pyglet
from .recompenses import PiluleForce
from .fantome import Fantome
from .fenetre_pyglet import Fenetre
from .obstacles import Porte
from .paxman import Paxman
from .plateau import Plateau
from .son_pyglet import Son, LecteurSon


class JeuPaxman:
    """Classe qui encapsule les composantes du jeu Paxman.

    Ces composantes sont:
    1. le plateau de jeu;
    2. le Paxman;
    3. la liste de fantômes;
    4. la fenêtre graphique du jeu;
    5. et réglages du jeu.
    """

    def __init__(self, niveau: int, sourdine: bool = False):
        self._sourdine = sourdine
        # déterminer le chemin du fichier des réglages pour le niveau demandé
        path = pathlib.Path(__file__).parent / "niveaux" / f"niveau{niveau}.json"

        # ouvrir le fichier de niveau et lire son contenu
        with path.open("r", encoding="utf-8") as fichier:
            config = json.load(fichier)

        # mémoriser les réglages du jeu
        self._reglages = config["réglages"]

        # initialiser le plateau de jeu
        self._plateau = Plateau(description=config["plateau"])

        # créer le Paxman
        self._paxman = Paxman(
            *config["paxman"]["position-initiale"],
            reglages=config["paxman"],
        )

        # créer les fantômes
        self._fantomes = {}
        for reglages in config["fantômes"]:
            # ajouter le fantôme au dictionnaire de fantômes
            self._fantomes[reglages["nom"]] = Fantome(
                *reglages["position-initiale"],
                reglages=reglages,
            )

        # initialiser la fenêtre d'affichage
        self._fenetre = Fenetre(self.plateau, self._reglages, caption="Jeu de Paxman")

        # programmer l'appel de la méthode d'animation du jeu
        self.fenetre.programmer_appel_fonction(
            self.animer_le_jeu,
            1 / 60,
            intervalle=True,
        )

        # programmer l'ouverture automatique des portes
        self.fenetre.programmer_appel_fonction(
            self.ouvrir_les_portes,
            self._reglages["porte-délai-ouverture"],
        )

        # passer en mode dispersion
        self.mode = None
        self.alterner_dispersion_poursuite(0)
        self._sons = {
            "sirene": LecteurSon(Son.SIRENE, en_boucle=True),
            "mange-pilule": LecteurSon(Son.MANGE_PILULE, volume=0.5),
            "mange-fantome": LecteurSon(Son.MANGE_FANTOME),
            "paxman-requiem": LecteurSon(Son.PAXMAN_REQUIEM),
            "fantomes-enfuite": LecteurSon(Son.FANTOMES_ENFUITE, en_boucle=True, volume=0.5),
        }

        self.jouer_son("sirene")
        self._sourdine = sourdine
        if self._sourdine:
            for son in self._sons.values():
                son.arreter()
        self.timer_fuite = 0

    @property
    def fenetre(self) -> Fenetre:
        """Retourne la fenêtre graphique de ce jeu."""

        return self._fenetre

    @property
    def fantomes(self) -> dict[str, Fantome]:
        """Retourne les fantômes de ce jeu, sous la forme d'un dictionnaire indexé
        par le nom du fantôme."""

        return self._fantomes

    @property
    def paxman(self) -> Paxman:
        """Retourne le Paxman de ce jeu."""

        return self._paxman

    @property
    def plateau(self) -> Plateau:
        """Retourne le plateau de ce jeu."""

        return self._plateau

    @property
    def manette(self) -> tuple[int, int]:
        """Retourne la direction actuelle de la manette de jeu."""

        return self.fenetre.manette

    def reglage(self, titre: str) -> int | float | str | tuple | list:
        """Retourne le réglage associé au titre spécifié."""

        return self._reglages[titre]
    def animer_le_jeu(self, delta_t: float | None = None) -> None:
        """Anime Trame de jeu."""
        if delta_t is None:
            delta_t = 0

    # 1. Déplacer Paxman
        direction = self.paxman.choisir_une_direction(self)
        if getattr(self, "mode_auto", False):
            direction = self.paxman.choisir_une_direction(self)
        else:
            direction = self.manette

        self.paxman.deplacer(direction, delta_t, self.plateau)

    # 2. Vérifier si Paxman mange une récompense
        recompense_mangee = None
        case_paxman = tuple(self.paxman.tuile_courante())

        for recompense in self.plateau.recompenses:
            if tuple(recompense.position) == case_paxman:
                recompense_mangee = recompense
                break

        if recompense_mangee is not None:
            self.paxman.score += recompense_mangee.points
            del self.plateau[recompense_mangee.position]
            self.jouer_son("mange-pilule")
        # Supprimer l'ancien dessin des récompenses
            self._fenetre.effacer_recompenses()

        # Redessiner les récompenses
            self.fenetre.dessiner_recompenses(self.plateau)

        # Si c'est une pilule de force
            if isinstance(recompense_mangee, PiluleForce):
            # Annuler les appels déjà programmés
                self.fenetre.annuler_appel_fonction(
                    self.alterner_dispersion_poursuite
            )
                self.fenetre.annuler_appel_fonction(
                    self.signaler_fin_vulnerabilite
            )
                self.fenetre.annuler_appel_fonction(
                    self.terminer_effet_pilule_force
            )

            # Accélérer Paxman
                self.paxman.vitesse = self.paxman.reglage("vitesse-force")
                self._sons["sirene"].arreter()
                self.jouer_son("fantomes-enfuite")

            # Mettre les fantômes en fuite
                for fantome in self.fantomes.values():
                    if fantome.mode != "revenant":
                        fantome.mode = "fuite"
                        fantome.mutation = False

            # Programmer l'avertissement à 80 % de la durée
                # Programmer l'avertissement à 80 % de la durée
                duree = self._reglages["fuite-durée"]
                self.fenetre.programmer_appel_fonction(
                    self.signaler_fin_vulnerabilite,
                    0.8 * duree,
                )

# Programmer la fin de l'effet
                self.fenetre.programmer_appel_fonction(
                    self.terminer_effet_pilule_force,
                    duree,
                )

    # 3. Déplacer les fantômes
        for fantome in self.fantomes.values():
            direction = fantome.choisir_une_direction(self)
            fantome.deplacer(direction, delta_t, self.plateau)

    # 4. Vérifier les collisions
        case_paxman = tuple(self.paxman.tuile_courante())

        for fantome in self.fantomes.values():
            if self.paxman.calculer_distance_l1(fantome.position) <= 0.5:
                if fantome.mode == "fuite":
                    self.paxman.score += 200
                    fantome.mode = "revenant"
                    fantome.mutation = False
                    self.jouer_son("mange-fantome")
                elif fantome.mode != "revenant":
                    self.sauvegarder_score()
                    self._sons["sirene"].arreter()
                    self._sons["fantomes-enfuite"].arreter()
                    self.jouer_son("paxman-requiem")
                    self.sauvegarder_score()
                    raise StopIteration("Partie perdue")

    # 5. Vérifier la victoire
        if not any(True for _ in self.plateau.recompenses):
            self.sauvegarder_score()
            raise StopIteration("Partie gagnée")

    # 6. Mettre à jour l'affichage du score
        self.fenetre.score.text = f"Score: {self.paxman.score}"

    # 7. Redessiner Paxman et les fantômes
    # pylint: disable=protected-access
        if "paxman" in self.fenetre._primitives_acteur:
            self.fenetre._primitives_acteur["paxman"].delete()

        for fantome in self.fantomes.values():
            if fantome.nom in self.fenetre._primitives_acteur:
                for primitive in self.fenetre._primitives_acteur[fantome.nom]:
                    primitive.delete()
    # pylint: enable=protected-access

        self.fenetre.dessiner_paxman(self.paxman)

        for fantome in self.fantomes.values():
            self.fenetre.dessiner_fantome(fantome)
        
        if isinstance(recompense, PiluleForce):
            for fantome in self._fantomes.values():
                fantome.mode = "fuite"

            self.timer_fuite = 8
        if self.timer_fuite > 0:
            self.timer_fuite -= delta_t

    def alterner_dispersion_poursuite(self, _delta_t: float) -> None:
        """Alterne entre le mode de jeu entre dispersion et poursuite."""

        if self.mode is None or self.mode == "poursuite":
            self.mode = "dispersion"

            for fantome in self.fantomes.values():
                if fantome.mode != "revenant":
                    fantome.mode = "dispersion"

            self.fenetre.programmer_appel_fonction(
                self.alterner_dispersion_poursuite,
                self._reglages["dispersion-durée"],
        )

        else:
            self.mode = "poursuite"

            for fantome in self.fantomes.values():
                if fantome.mode != "revenant":
                    fantome.mode = "poursuite"

            self.fenetre.programmer_appel_fonction(
                self.alterner_dispersion_poursuite,
                self._reglages["poursuite-durée"],
        )

    def terminer_effet_pilule_force(self, _delta_t: float) -> None:
        """Termine l'effet temporaire de la pilule force."""

        self.paxman.vitesse = self.paxman.reglage("vitesse-défaut")

        for fantome in self.fantomes.values():
            if fantome.mode != "revenant":
                # retourner le fantôme dans le mode actuel du jeu
                fantome.mode = self.mode

        self.fenetre.annuler_appel_fonction(self.alterner_dispersion_poursuite)
        self.fenetre.programmer_appel_fonction(
            self.alterner_dispersion_poursuite,
            self._reglages[f"{self.mode}-durée"],
        )
        self._sons["fantomes-enfuite"].arreter()
        self.jouer_son("sirene")

    def signaler_fin_vulnerabilite(self, _delta_t: float) -> None:
        """Avertit que la vulnérabilité des fantômes va bientôt se terminer."""

        for fantome in self.fantomes.values():
            # activer la mutation du fantôme en fuite
            fantome.mutation = fantome.mode == "fuite"

    def ouvrir_les_portes(self, _delta_t: float) -> None:
        """Ouvre toutes les portes."""

        # boucler sur tous les objets du tableau
        for obj in self.plateau.obstacles:
            if isinstance(obj, Porte):
                obj.ouverture = True

        # redessiner les obstacles du plateau
        self.fenetre.dessiner_obstacles(self.plateau)

    def en_cage(self, pos: tuple[float, float]) -> bool:
        """Détermine si la position reçue est à l'intérieur de la cage."""

        # obtenir les coordonnées de la position
        x, y = pos

        # obtenir les coordonnées de la cage
        (x1, y1), (x2, y2) = self.reglage("emplacement-cage")

        # retourner si oui ou non l'acteur est en cage
        return x1 <= x <= x2 and y1 <= y <= y2

    def demarrer_boucle_evenements(self) -> None:
        """Démarre la boucle événementielle du jeu."""

        pyglet.app.run()

    def sauvegarder_score(self) -> None:
        """Sauvegarde le score courant dans scores.txt."""
        path = pathlib.Path("scores.txt")

        horodatage = datetime.now().isoformat(timespec="seconds")
        ligne = f"{horodatage} {self.paxman.score}\n"

        with path.open("a", encoding="utf-8") as fichier:
            fichier.write(ligne)
    def jouer_son(self, nom):
        """Joue un son si le mode sourdine n'est pas activé."""
        if not self._sourdine:
            self._sons[nom].jouer()
