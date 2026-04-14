"""Ce module contient la définition de la classe qui encapsule la fenêtre graphique de jeu."""

import math
import time
from collections.abc import Callable

import numpy as np
import pyglet

from .fantome import Fantome
from .obstacles import Mur, Porte
from .paxman import Paxman
from .plateau import Plateau
from .recompenses import Pilule

# couleurs prédéfinies
COULEURS = {
    "rouge": (255, 0, 0, 255),
    "rose": (255, 192, 203, 255),
    "bleu": (0, 0, 255, 255),
    "cyan": (0, 255, 255, 255),
    "vert": (0, 255, 0, 255),
    "orange": (255, 180, 0, 255),
    "blanc": (255, 255, 255, 255),
    "jaune": (255, 255, 0, 255),
    "noir": (0, 0, 0, 255),
}


class Fenetre(pyglet.window.Window):
    """Cette classe encapsule toutes les fonctionnalités graphiques du jeu de Paxman."""

    # pylint: disable=too-many-instance-attributes

    def __init__(self, plateau: Plateau, reglages: dict[str, str | float], **kwargs) -> None:
        """Construire une fenêtre graphique."""

        # initialiser la fenêtre pyglet
        super().__init__(
            plateau.largeur * reglages["tuile-dimension"],
            plateau.hauteur * reglages["tuile-dimension"],
            **kwargs,
        )

        # mémoriser les réglages
        self._reglages = reglages

        # initialiser la référence de temps
        self._timeref = time.perf_counter()

        # initialiser la direction actuelle de la manette
        self.manette = (0, 0)

        # initialiser la projection pour l'espace des pixels (origine en bas à gauche; défaut)
        self._projection_pixels = pyglet.math.Mat4.orthogonal_projection(
            left=0,
            right=self.width,
            bottom=0,
            top=self.height,
            z_near=-1,
            z_far=+1,
        )

        # initialiser la projection pour l'espace des tuiles (origine en bas à gauche)
        self.projection = self._projection_tuiles = pyglet.math.Mat4.orthogonal_projection(
            left=0,
            right=plateau.largeur + 1,
            bottom=0,
            top=plateau.hauteur + 1,
            z_near=-1,
            z_far=+1,
        )

        # définir une batch pyglet pour le dessin des objets du plateau
        self._batch = pyglet.graphics.Batch()

        # définir un groupe pour les objets statiques du tableau
        self._groupe_statique = pyglet.graphics.Group(order=0)

        # définir un groupe pour le paxman
        self._groupe_paxman = pyglet.graphics.Group(order=1)

        # définir un groupe pour les fantômes
        self._groupe_fantomes = pyglet.graphics.Group(order=2)

        # définir un groupe pour les yeux des fantômes
        self._groupe_yeux = pyglet.graphics.Group(order=3)

        # dessiner les graphiques des obstacles du plateau
        self.dessiner_obstacles(plateau)

        # dessiner les graphiques des récompenses du plateau
        self.dessiner_recompenses(plateau)

        # initialiser un dictionnaire pour les primitives graphiques des acteurs
        self._primitives_acteur: dict[str, list[pyglet.shapes.ShapeBase]] = {}

        # créer l'affichage du score
        self.score = self.dessiner_score()

        # créer l'affichage du taux de rafraîchissement
        self.fps = self.dessiner_fps()

        if reglages.get('afficher-cage'):
            # dessiner la cage des fantômes
            self.cage = self.dessiner_cage(reglages['emplacement-cage'])

    def temps_ecoule(self) -> float:
        """Retourne le temps écoulé (en secondes) depuis la construction de cette fenêtre."""

        return time.perf_counter() - self._timeref

    def dessiner_obstacles(self, plateau: Plateau) -> None:
        """Crée les formes graphiques pour le dessin des obstacles du plateau."""

        # initialiser un contenant pour les formes graphiques des obstacles
        self._primitives_obstacles = []

        # boucler sur tous les obstacles du plateau
        for obj in plateau.obstacles:
            match obj:
                case Mur(_sorte="─"):
                    # mur horizontal
                    x, y = obj.position
                    dim = obj.dimension / 2
                    self._primitives_obstacles.append(
                        pyglet.shapes.Line(
                            x - dim,
                            y,
                            x + dim,
                            y,
                            thickness=self._reglages["mur-épaisseur"],
                            color=COULEURS['bleu'],
                            batch=self._batch,
                            group=self._groupe_statique,
                        )
                    )

                case Porte(_sorte="_"):
                    # porte horizontale
                    x, y = obj.position
                    dim = obj.dimension / 2
                    self._primitives_obstacles.append(
                        pyglet.shapes.Line(
                            x - dim,
                            y,
                            x + dim,
                            y,
                            thickness=self._reglages["mur-épaisseur"] / 3,
                            color=COULEURS['rose'] if obj.ouverture else COULEURS['bleu'],
                            batch=self._batch,
                            group=self._groupe_statique,
                        )
                    )

                case Mur(_sorte="│"):
                    # mur vertical
                    x, y = obj.position
                    dim = obj.dimension / 2
                    self._primitives_obstacles.append(
                        pyglet.shapes.Line(
                            x,
                            y - dim,
                            x,
                            y + dim,
                            thickness=self._reglages["mur-épaisseur"],
                            color=COULEURS['bleu'],
                            batch=self._batch,
                            group=self._groupe_statique,
                        )
                    )

                case Porte(_sorte=":"):
                    # porte verticale
                    x, y = obj.position
                    dim = obj.dimension / 2
                    self._primitives_obstacles.append(
                        pyglet.shapes.Line(
                            x,
                            y - dim,
                            x,
                            y + dim,
                            thickness=self._reglages["mur-épaisseur"] / 3,
                            color=COULEURS['rose'] if obj.ouverture else COULEURS['bleu'],
                            batch=self._batch,
                            group=self._groupe_statique,
                        )
                    )

                case Mur(_sorte="┌"):
                    # coin supérieur gauche
                    x, y = obj.position
                    rayon = obj.dimension / 2
                    self._primitives_obstacles.append(
                        pyglet.shapes.Arc(
                            x + rayon,
                            y - rayon,
                            radius=rayon,
                            start_angle=90,
                            angle=90,
                            thickness=self._reglages["mur-épaisseur"],
                            color=COULEURS['bleu'],
                            batch=self._batch,
                            group=self._groupe_statique,
                        )
                    )

                case Mur(_sorte="┐"):
                    # coin supérieur droit
                    x, y = obj.position
                    rayon = obj.dimension / 2
                    self._primitives_obstacles.append(
                        pyglet.shapes.Arc(
                            x - rayon,
                            y - rayon,
                            radius=rayon,
                            start_angle=0,
                            angle=90,
                            thickness=self._reglages["mur-épaisseur"],
                            color=COULEURS['bleu'],
                            batch=self._batch,
                            group=self._groupe_statique,
                        )
                    )

                case Mur(_sorte="└"):
                    # coin inférieur gauche
                    x, y = obj.position
                    rayon = obj.dimension / 2
                    self._primitives_obstacles.append(
                        pyglet.shapes.Arc(
                            x + rayon,
                            y + rayon,
                            radius=rayon,
                            start_angle=180,
                            angle=90,
                            thickness=self._reglages["mur-épaisseur"],
                            color=COULEURS['bleu'],
                            batch=self._batch,
                            group=self._groupe_statique,
                        )
                    )

                case Mur(_sorte="┘"):
                    # coin inférieur droit
                    x, y = obj.position
                    rayon = obj.dimension / 2
                    self._primitives_obstacles.append(
                        pyglet.shapes.Arc(
                            x - rayon,
                            y + rayon,
                            radius=rayon,
                            start_angle=270,
                            angle=90,
                            thickness=self._reglages["mur-épaisseur"],
                            color=COULEURS['bleu'],
                            batch=self._batch,
                            group=self._groupe_statique,
                        )
                    )

                case _:
                    raise TypeError(f"type d'objet inconnu ou invalide': {type(obj).__name__}")


    def dessiner_recompenses(self, plateau: Plateau) -> None:
        """Crée les formes graphiques pour le dessin des récompenses du plateau."""

        # initialiser un contenant pour les formes graphiques des récompenses
        self._primitives_recompenses = []

        # boucler sur toutes les récompenses du plateau
        for obj in plateau.recompenses:
            match obj:
                case Pilule():
                    # cas d'une pilule normale ou d'invincibilité
                    x, y = obj.position
                    rayon = obj.dimension / 2
                    self._primitives_recompenses.append(
                        pyglet.shapes.Circle(
                            x,
                            y,
                            radius=rayon,
                            color=COULEURS['rose'],
                            batch=self._batch,
                            group=self._groupe_statique,
                        )
                    )

                case _:
                    raise TypeError(f"type d'objet inconnu ou invalide': {type(obj).__name__}")

    def dessiner_paxman(self, paxman: Paxman) -> None:
        """Crée les formes graphiques pour le dessin du Paxman."""

        # angles d'ouverture de la bouche de Paxman
        angles = [25, 40, 60]

        # position et rayon du paxman
        x, y = paxman.position
        r = 1.30 * paxman.dimension / 2

        # déterminer l'ouverture de la bouche
        if paxman.direction == (0, 0):
            ouverture = 0

        else:
            ouverture = angles[round(self.temps_ecoule() * 15) % len(angles)]

        # dessiner le paxman
        self._primitives_acteur['paxman'] = pyglet.shapes.Sector(
            x,
            y,
            radius=r,
            start_angle=ouverture / 2,
            angle=360 - ouverture,
            color=COULEURS['jaune'],
            batch=self._batch,
            group=self._groupe_paxman,
        )

        if paxman.direction == (0, 1):
            self._primitives_acteur['paxman'].rotation = -90

        elif paxman.direction == (0, -1):
            self._primitives_acteur['paxman'].rotation = 90

        elif paxman.direction == (-1, 0):
            self._primitives_acteur['paxman'].rotation = 180

        elif paxman.direction == (1, 0):
            self._primitives_acteur['paxman'].rotation = 0

    def dessiner_fantome(self, fantome: Fantome) -> None:
        """Crée les formes graphiques pour le dessin d'un fantôme."""

        # initialiser une liste de formes pour ce fantôme
        self._primitives_acteur[fantome.nom] = []

        # dessiner le corps du fantôme
        self.dessiner_corps_fantome(fantome)

        # ajouter les deux yeux
        self.dessiner_yeux_fantome(fantome)

        if fantome.reglage("afficher-cible"):
            if fantome.cible is not None:
                # dessiner la cible du fantôme
                self._primitives_acteur[fantome.nom].append(
                    pyglet.shapes.Line(
                        *fantome.position,
                        *fantome.cible,
                        thickness=0.025,
                        color=COULEURS['blanc'],
                        batch=self._batch,
                        group=self._groupe_statique,
                    )
                )

            if fantome.options is not None:
                # dessiner les options de direction
                for option in fantome.options:
                    # obtenir les coordonnées actuelle du fantôme
                    x, y = fantome.position

                    # ajouter la ligne pour cette option
                    self._primitives_acteur[fantome.nom].append(
                        pyglet.shapes.Line(
                            x,
                            y,
                            x + option[0],
                            y + option[1],
                            thickness=0.05,
                            color=COULEURS['blanc'],
                            batch=self._batch,
                            group=self._groupe_statique,
                        )
                    )

    def dessiner_corps_fantome(self, fantome: Fantome) -> None:
        """Crée les formes graphiques pour le corps d'un fantôme."""

        # position et dimension du fantôme
        x, y = fantome.position
        dim = fantome.dimension * 1.25

        # échantillonner l'ellipse de sa tête
        t = np.linspace(0, math.pi, 15)

        # calculer l'équation paramétrique de l'arc d'ellipse
        x_ellipse = x + (dim / 2) * np.cos(t)
        y_ellipse = y + (dim / 2) * np.sin(t)

        # créer une liste de sommets
        sommets = list(zip(x_ellipse, y_ellipse))

        # fixer le nombre de vague pour les pieds du paxman
        nombre_de_vagues = 6

        # déterminer laquelle des deux variantes de pieds à dessiner
        k = 0 if self.temps_ecoule() * 60 % 10 < 5 else 1

        # ajouter le côté gauche du corps
        sommets.append((x - dim / 2, y - dim / 2 - k * dim / nombre_de_vagues))

        # ajouter les pieds du fantôme sous forme de vagues
        for i in range(nombre_de_vagues + 1):
            sommet_x = x - dim / 2 + i * (dim / nombre_de_vagues)
            if (i + k) % 2 == 0:
                sommet_y = y - dim / 2 + dim / 10
            else:
                sommet_y = y - dim / 2 - dim / 10
            sommets.append((sommet_x, sommet_y))

        # créer le polygone du fantôme
        self._primitives_acteur[fantome.nom].append(
            pyglet.shapes.Polygon(
                *sommets,
                color=COULEURS[fantome.couleur(self.temps_ecoule())],
                batch=self._batch,
                group=self._groupe_fantomes,
            )
        )

    def dessiner_yeux_fantome(self, fantome: Fantome) -> None:
        """Crée les formes graphiques pour les yeux d'un fantôme."""

        # position et dimension du fantôme
        x, y = fantome.position
        dim = fantome.dimension * 1.25

        # ajouter les deux yeux
        for i in range(2):
            self._primitives_acteur[fantome.nom].append(
                pyglet.shapes.Ellipse(
                    x + (-0.2 + 0.4 * i) * dim,
                    y + 0.05 * dim,
                    a=dim / 6,
                    b=dim / 5,
                    segments=14,
                    color=COULEURS['blanc'],
                    batch=self._batch,
                    group=self._groupe_yeux,
                )
            )

        # ajouter les deux pupilles
        for i in range(2):
            self._primitives_acteur[fantome.nom].append(
                pyglet.shapes.Circle(
                    x + (-0.2 + 0.4 * i) * dim,
                    y + 0.05 * dim,
                    radius=dim / 10,
                    color=COULEURS['noir'],
                    batch=self._batch,
                    group=self._groupe_yeux,
                )
            )

            # ajuster la positon des pupilles en fonction de la direction
            if fantome.direction == (0, 1):
                self._primitives_acteur[fantome.nom][-1].y += 0.2 * dim

            elif fantome.direction == (0, -1):
                self._primitives_acteur[fantome.nom][-1].y -= 0.2 * dim

            elif fantome.direction == (-1, 0):
                self._primitives_acteur[fantome.nom][-1].x -= 0.15 * dim

            elif fantome.direction == (1, 0):
                self._primitives_acteur[fantome.nom][-1].x += 0.15 * dim

    def dessiner_score(self) -> pyglet.text.Label:
        """Crée une étiquette graphique pour l'affichage du score."""

        return pyglet.text.Label(
            "Score: 0",
            font_name="Times New Roman",
            font_size=20,
            x=self.width / 2,
            y=self.height,
            anchor_x="center",
            anchor_y="top",
        )

    def dessiner_fps(self) -> pyglet.text.Label:
        """Crée une étiquette graphique pour l'affichage du nombre de trames par secondes."""

        return pyglet.text.Label(
            "fps: 0",
            font_name="Times New Roman",
            font_size=12,
            x=self.width - 5,
            y=5,
            anchor_x="right",
            anchor_y="bottom",
        )

    def dessiner_cage(self, emplacement: tuple[tuple[float, float], tuple[float, float]]) -> None:
        """Crée un rectangle translucide au dessus de la cage des fantômes."""

        # obtenir les coordonnées de la cage
        (x1, y1), (x2, y2) = emplacement

        return pyglet.shapes.Rectangle(
            x1,
            y1,
            x2 - x1,
            y2 - y1,
            (255, 255, 255, 20),
            batch=self._batch,
        )

    def programmer_appel_fonction(
        self, fonction: Callable, delai: float, intervalle: bool = False
    ) -> None:
        """Programme l'appel de la fonction reçue en argument à la fin du délai
        (spécifié en secondes)."""

        if intervalle:
            pyglet.clock.schedule_interval(fonction, delai)

        else:
            pyglet.clock.schedule_once(fonction, delai)

    def annuler_appel_fonction(self, fonction: Callable) -> None:
        """Annule l'appel de la fonction reçue en argument. Si aucun appel n'a
        été programmé pour cette fonction, on retourne sans rien faire"""

        pyglet.clock.unschedule(fonction)

    def on_draw(self) -> None:
        """Gérer l'événement de dessin de la fenêtre."""

        # effacer la fenêtre
        self.clear()

        # passer dans l'espace des tuiles
        self.projection = self._projection_tuiles

        if hasattr(self, "_batch"):
            # afficher les objets statiques du plateau
            self._batch.draw()

        # Revenir à l'espace des pixels
        self.projection = self._projection_pixels

        # afficher le score du paxman
        self.score.draw()

        # afficher le taux de rafraîchissement
        self.fps.text = f"fps={round(pyglet.clock.get_frequency(), 1)}"
        self.fps.draw()

    def on_key_press(self, symbol: int, _modifiers: int) -> None:
        """Gérer l'événement de pression d'une touche."""

        if symbol == pyglet.window.key.ESCAPE:
            pyglet.app.exit()

        elif symbol == pyglet.window.key.LEFT:
            self.manette = (-1, 0)

        elif symbol == pyglet.window.key.RIGHT:
            self.manette = (1, 0)

        elif symbol == pyglet.window.key.UP:
            self.manette = (0, 1)

        elif symbol == pyglet.window.key.DOWN:
            self.manette = (0, -1)

    def on_key_release(self, symbol: int, _modifiers) -> None:
        """Gérer l'événement de relâchement d'une touche."""

        if symbol == pyglet.window.key.ESCAPE:
            pyglet.app.exit()

        elif symbol == pyglet.window.key.LEFT:
            if self.manette == (-1, 0):
                self.manette = (0, 0)

        elif symbol == pyglet.window.key.RIGHT:
            if self.manette == (1, 0):
                self.manette = (0, 0)

        elif symbol == pyglet.window.key.UP:
            if self.manette == (0, 1):
                self.manette = (0, 0)

        elif symbol == pyglet.window.key.DOWN:
            if self.manette == (0, -1):
                self.manette = (0, 0)
    def effacer_recompenses(self):
        """Efface les récompenses affichées."""
        for primitive in self._primitives_recompenses:
            primitive.delete()
        self._primitives_recompenses.clear()
