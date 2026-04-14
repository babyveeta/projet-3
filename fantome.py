"""Ce module contient la définition de la classe qui encapsule les fantômes du jeu Paxman."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

from .acteur import Acteur

if TYPE_CHECKING:
    from .jeu import JeuPaxman


class Fantome(Acteur):
    """Un fantôme est un acteur qui tente de rattraper Paxman afin de le tuer."""

    # pylint: disable=too-many-instance-attributes

    # ensemble des modes comportementaux des fantômes
    MODES = {
        "dispersion",  # le fantôme cible son coin de référence
        "poursuite",  # le fantôme poursuit Paxman
        "fuite",  # le fantôme fuit Paxman
        "revenant",  # le fantôme retourne à l'entrée de la cage après avoir été tué
    }

    def __init__(self, x: int, y: int, *, reglages: dict[str, str | float | int]) -> None:
        """Initialise l'état interne de ce fantôme."""

        # initialiser la position de l'acteur sous-jacent
        super().__init__(x, y)

        # initialiser la direction vers le haut
        self.direction = (0, 1)

        # mémoriser les réglages du fantôme
        self._reglages = reglages

        # initialiser la cible pour le débogage
        self._cible = None

        # initialiser les options de direction pour le débogage
        self._options = None

    @property
    def options(self) -> list[tuple[int, int]] | None:
        """Retourne les dernières options de direction de ce fantôme."""

        return self._options

    @options.setter
    def options(self, valeur: list[tuple[int, int]] | None) -> None:
        """Actualise les options de direction de ce fantôme."""

        self._options = valeur

    @property
    def cible(self) -> tuple[float, float] | None:
        """Retourne la dernière cible de ce fantôme."""

        return self._cible

    @cible.setter
    def cible(self, valeur: tuple[float, float] | None) -> None:
        """Actualise la cible de ce fantôme."""

        self._cible = valeur

    @property
    def nom(self) -> str:
        """Retourne le nom de ce fantôme."""

        return self.reglage("nom")

    @property
    def mode(self) -> str | None:
        """Retourne le mode comportemental de ce fantôme."""

        return getattr(self, "_mode", None)

    @mode.setter
    def mode(self, valeur: str | None) -> None:
        """Actualise le mode comportemental de ce fantôme."""

        # valider la valeur
        if valeur not in Fantome.MODES:
            raise ValueError(f"mode {valeur!r} invalide (doit être choisi parmi {Fantome.MODES})")

        # actualiser le mode comportemental
        self._mode = valeur

        # ajuster les paramètres spécifiques au mode
        if valeur == "fuite":
            # inverser la direction du fantôme
            self.direction = self.demi_tour()

            # ajuster la vitesse de fuite
            self.vitesse = self.reglage("vitesse-fuite")

        elif valeur == "revenant":
            # ajuster la vitesse du fantôme pour le mode revenant
            self.vitesse = self.reglage("vitesse-revenant")

        else:
            # ajuster la vitesse pour les modes cage, poursuite et dispersion
            self.vitesse = self.reglage("vitesse-défaut")

        # désactiver toute mutation en cours
        self._mutation = False

    @property
    def mutation(self) -> bool:
        """Retourne l'état de mutation pour ce fantôme."""

        return getattr(self, "_mutation", False)

    @mutation.setter
    def mutation(self, valeur: bool) -> None:
        """Actualise l'état de mutation pour ce fantôme."""

        self._mutation = valeur

    def couleur(self, temps: float) -> str:
        """Retourne la couleur de ce fantôme selon son mode comportemental.

        En poursuite et dispersion, la couleur est spécifique à chaque fantôme:
        + Blinky est rouge;
        + Pinky est rose;
        + Inky est cyan;
        + Clyde est orange.

        En revenant, tous les fantômes sont noirs.

        En fuite, tous les fantômes sont bleus, mais clignotent en blanc lorsqu'en mutation.
        """

        if self.mode in ["poursuite", "dispersion"]:
            if self.nom == "Blinky":
                return "rouge"

            if self.nom == "Pinky":
                return "rose"

            if self.nom == "Inky":
                return "cyan"

            if self.nom == "Clyde":
                return "orange"

        elif self.mode == "revenant":
            return "noir"

        elif self.mode == "fuite":
            return "bleu" if not self.mutation or temps * 60 % 14 < 7 else "blanc"

        raise ValueError(
            f"mode de comportement {self.mode!r} invalide pour le calcul de la couleur du fantôme"
        )

    def choisir_une_direction(self, jeu: JeuPaxman) -> tuple[int, int]:
        """Choisit une direction pour le fantôme selon son mode comportemental.

        En mode fuite, le fantôme choisit une direction aléatoire parmi les options admissibles.

        Dans les autres modes, il choisit la direction qui minimise la distance avec sa cible.
        """

        if self.mode == "fuite":
            # aucune cible en mode fuite
            self.cible = None

            # trouver les directions admissibles
            self.options = self._lister_directions_possibles(jeu)

            # choisir une direction aléatoire parmi les options disponibles
            direction = random.choices(self.options)[0]

        else:
            # choisir la cible actuelle du fantôme
            self.cible = self._calculer_la_cible(jeu)

            # comportement historique: algorithme glouton local
            direction = self._choisir_direction_gloutonne(jeu, self.cible)

        # retourner le vecteur de direction choisie
        return direction

    def _choisir_direction_gloutonne(
        self, jeu: JeuPaxman, cible: tuple[float, float]
    ) -> tuple[int, int]:
        """Choisit la prochaine direction via la stratégie gloutonne."""
        # obtenir les coordonnées de ce fantôme
        x, y = self.position

        # initialiser une variable d'accumulation pour le calcul des distances
        distances = []

        # déterminer les options de direction
        self.options = self._lister_directions_possibles(jeu)

        # pour chaque option de direction, calculer les distances avec la cible
        for dx, dy in self.options:
            # créer un acteur temporaire à cette position
            acteur = Acteur(x + dx, y + dy)

            # calculer la distance entre cet acteur et la cible
            distances.append((acteur.calculer_distance_l1(cible), (dx, dy)))

        # choisir la direction qui minimise la distance
        return min(distances, key=lambda x: x[0])[1]

    def _calculer_la_cible(self, jeu: JeuPaxman) -> tuple[float, float]:
        """Choisit la cible actuelle pour ce fantôme.

        En mode dispersion, la cible est spécifiée dans les réglages du fantôme.

        En mode poursuite, la cible est spécifique à chaque fantôme:
        + Blinky cible directement la tuile qu'occupe Paxman;
        + Pinky cible toujours 4 tuiles devant Paxman;
        + Inky cible la tuile du Paxman additionnée du vecteur qui relie Blinky à Paxman;
        + Clyde cible 2 tuiles devant Paxman, mais à condition d'être à plus de
          8 tuiles de distance. Sinon, il utilise sa cible de dispersion.

        En mode fuite, il n'y a pas de cible à fixer, car la direction est choisit aléatoirement.

        En mode revenant, la cible est la position initiale du fantôme,
        mais avec une cible intermédiaire pour accéder à l'entrée de la cage.

        Cette méthode est utilisée à l'interne par la méthode `choisir_une_direction`.
        """
        cible: tuple[float, float] | None = None

        if self.mode == "dispersion":
            if jeu.en_cage(self.position):
                # fantôme en cage; cibler la sortie de celle-ci
                cible = jeu.reglage("cible-cage")

            else:
                # la cible de dispersion est spécifiée dans les réglages du fantôme
                cible = self.reglage("cible-dispersion")

        elif self.mode == "poursuite":
            # la cible de poursuite est spécifique à chaque fantôme
            cible = self._calculer_cible_en_poursuite(jeu)

        elif self.mode == "revenant":
            if jeu.en_cage(self.position):
                # fantôme en cage; cibler sa position initiale
                cible = self.reglage("position-initiale")

            else:
                # cibler l'entrée de la cage
                cible = jeu.reglage("cible-cage")

            if self.calculer_distance_l1(self.reglage("position-initiale")) <= 0.5:
                # le fantôme a atteint sa position initiale; passer dans le mode actuel du jeu
                self.mode = jeu.mode

        if cible is None:
            raise ValueError(
                f"mode de comportement {self.mode!r} invalide pour le calcul de la cible"
            )

        # retourner la cible
        return cible

    def _calculer_cible_en_poursuite(self, jeu: JeuPaxman) -> tuple[float, float]:
        """Choisit la cible actuelle pour ce fantôme lorsqu'en mode poursuite.

        En mode poursuite, la cible est spécifique à chaque fantôme:
        + Blinky cible directement la tuile qu'occupe Paxman;
        + Pinky cible toujours 4 tuiles devant Paxman;
        + Inky cible la tuile du Paxman additionnée du vecteur qui relie Blinky à Paxman;
        + Clyde cible 2 tuiles devant Paxman, mais à condition d'être à plus de
          8 tuiles de distance. Sinon, il utilise sa cible de dispersion.

        Cette méthode est utilisée à l'interne par la méthode `_calculer_la_cible`.
        """

        # initialiser la cible pour le mode poursuite
        cible: tuple[float, float] | None = None

        if self.mode != "poursuite":
            raise ValueError(f"mode comportemental {self.mode!r} invalide (doit être 'poursuite')")

        if jeu.en_cage(self.position):
            # fantôme en cage; cibler la sortie de celle-ci
            cible = jeu.reglage("cible-cage")

        else:
            # appliquer la stratégie spécifique de chaque fantôme
            if self.nom == "Blinky":
                # la cible de Blinky est la position de Paxman
                cible = jeu.paxman.position

            elif self.nom == "Pinky":
                # Pinky part de la position de Paxman
                x, y = jeu.paxman.position

                # et cible quatre tuiles devant lui
                dx, dy = jeu.paxman.direction
                cible = (x + 4 * dx, y + 4 * dy)

            elif self.nom == "Inky":
                # Inky part de la position de Paxman
                x, y = jeu.paxman.position

                # puis cible deux tuiles devant lui
                dx, dy = jeu.paxman.direction
                x, y = (x + 2 * dx, y + 2 * dy)

                # puis calcule le vecteur qui relie Paxman à Blinky
                dx, dy = jeu.paxman.calculer_vecteur(jeu.fantomes["Blinky"].position)

                # et soustrait ce vecteur pour obtenir la cible finale
                cible = (x - dx, y - dy)

            elif self.nom == "Clyde":
                if self.calculer_distance_l1(jeu.paxman.position) >= 8:
                    # lorsqu'il est loin de Paxman, Clyde cible 2 tuiles devant Paxman
                    x, y = jeu.paxman.position
                    dx, dy = jeu.paxman.direction
                    cible = (x + 2 * dx, y + 2 * dy)

                else:
                    # lorsqu'il est proche, il utilise la cible du mode dispersion
                    cible = self.reglage("cible-dispersion")

        # retourner la cible
        return cible

    def _lister_directions_possibles(self, jeu: JeuPaxman) -> list[tuple[int, int]]:
        """Retourne la liste des directions que le fantôme peut actuellement prendre.

        Cette méthode est utilisée à l'interne par la méthode `choisir_une_direction`.
        """

        # obtenir les coordonnées de la position actuelle du fantôme
        x, y = self.position

        # obtenir son vecteur actuel de direction
        dx, dy = self.direction

        # calculer le vecteur de direction par rapport au centre de la tuile
        vx, vy = round(x) - x, round(y) - y

        # tester le produit scalaire
        if dx * vx + dy * vy >= 0:
            # le fantôme se dirige vers le centre de la tuile; initialiser variable d'accumulation
            options = set()

            # tester les directions tout droit, virage à gauche et virage à droite
            for di, dj in [self.direction, self.virage_gauche(), self.virage_droite()]:
                if not jeu.plateau.tuile_franchissable((x+di, y+dj)):
                    # ne pas considérer cette direction
                    continue

                if (
                    self.mode != "revenant"
                    and jeu.en_cage((x+di, y+dj))
                    and not jeu.en_cage(self.position)
                ):
                    # un fantôme hors de sa cage ne peut y revenir, sauf en mode revenant
                    continue

                # ajouter l'option de cette direction
                options.add((di, dj))

        else:
            # le fantôme s'éloigne du centre; conserver la direction courante
            options = {self.direction}

        if not options:
            # aucune option trouvée; faire demi-tour
            options.add(self.demi_tour())

        # retourner la liste des options trouvées
        return list(options)
