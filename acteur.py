"""Ce module contient la définition de la classe qui encapsule les acteurs du jeu Paxman."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .objet import Objet

if TYPE_CHECKING:
    from .plateau import Plateau


class Acteur(Objet):
    """
    Un acteur est un objet capable de se déplacer sur le plateau de jeu.

    Il peut se déplacer vers le haut, vers le bas, vers la gauche ou vers la droite.

    Sa vitesse est exprimée en tuiles / seconde.
    """

    # ensemble des directions admissibles
    DIRECTIONS = {(0, 0), (0, 1), (0, -1), (1, 0), (-1, 0)}

    def __init__(self, x: float, y: float) -> None:
        # initialiser la position de l'acteur
        super().__init__(x, y)

        # définir sa direction initiale
        self.direction = (0, 0)

        # définir sa vitesse par défaut
        self.vitesse = 0

        # initialiser ses réglages
        self._reglages = {}

    @property
    def direction(self) -> tuple[int, int]:
        """Retourne la direction actuelle de l'acteur."""

        return self._dir

    @direction.setter
    def direction(self, direction: tuple[int, int]) -> None:
        """Définit la direction de l'acteur."""

        # valider le tuple reçue
        if direction not in self.DIRECTIONS:
            raise ValueError(
                f"direction {direction!r} invalide (doit être choisi parmi {self.DIRECTIONS})"
            )

        # mémoriser la nouvelle direction
        self._dir = direction

    @property
    def vitesse(self) -> float:
        """Retourne la vitesse actuelle de l'acteur."""

        return self._vit

    @vitesse.setter
    def vitesse(self, vit: float) -> None:
        """Définit la vitesse de l'acteur."""

        # valider la vitesse reçue
        if vit < 0:
            raise ValueError("vitesse invalide (doit être > 0)")

        # mémoriser la nouvelle vitesse
        self._vit = vit

    def reglage(self, titre: str) -> int | float | str | tuple | list:
        """Retourne le réglage associé au titre spécifié."""

        return self._reglages[titre]

    def virage_gauche(self) -> tuple[int, int]:
        """Retourne le vecteur de direction pour un virage à gauche."""

        return (-self._dir[1], self._dir[0])

    def virage_droite(self) -> tuple[int, int]:
        """Retourne le vecteur de direction pour un virage à droite."""

        return (self._dir[1], -self._dir[0])

    def demi_tour(self) -> tuple[int, int]:
        """Retourne le vecteur de direction pour un demi-tour."""

        return (-self._dir[0], -self._dir[1])

    def tuile_courante(self) -> tuple[int, int]:
        """Retourne les coordonnées de la tuile actuelle de l'acteur."""

        return (round(self._pos[0]), round(self._pos[1]))

    def deplacer(self, direction: tuple[int, int], delta_t: float, plateau: Plateau) -> None:
        """Actualise la position de l'acteur selon la direction spécifiée,
        en utilisant le temps écoulé (delta_t) et le contenu du plateau.

        Notez que les virages ne peuvent se faire qu'aux deux conditions suivantes:
        1. l'acteur se déplace actuellement vers le centre de sa tuile;
        2. aucun obstacle ne se trouve dans la direction du virage.

        Cette méthode ne retourne jamais rien.
        """

        if self.direction == (0, 0):
            # aucune direction actuelle; initialiser avec la direction demandée
            self.direction = direction

        elif direction == (0, 0):
            # aucune direction demandée; continuer dans la direction courante
            direction = self.direction

        if direction == (0, 0) or self.direction == (0, 0):
            # aucune direction actuelle ni demandée; ne rien faire
            return None

        # obtenir les composantes de la position actuelle de l'acteur
        x, y = self.position

        # obtenir les coordonnées du centre de la tuile de l'acteur
        i, j = self.tuile_courante()

        # calculer la distance à parcourir (max 1 tuile)
        dap = min(self.vitesse * delta_t, 1)

        # obtenir les composantes du vecteur unitaire de direction courante (dc)
        dc_i, dc_j = self.direction

        # obtenir les composantes du vecteur unitaire de direction demandée (dd)
        dd_i, dd_j = direction

        # calculer le produit scalaire des deux vecteurs unitaires
        if dc_i * dd_i + dc_j * dd_j == 0:
            # un produit scalaire nul implique un virage à droite ou à gauche;
            # tester si le virage est possible; on ne peut virer qu'au centre d'une tuile
            if (
                (x <= i <= x + dc_i * dap or x >= i >= x + dc_i * dap)
                and (y <= j <= y + dc_j * dap or y >= j >= y + dc_j * dap)
                and plateau.tuile_franchissable((i + dd_i, j + dd_j))
            ):
                # poursuivre la trajectoire courante jusqu'au centre de la tuile
                x, y = i, j

                # ajuster la distance qui reste à parcourir
                dap -= abs(i - x + j - y)

                # virer dans la direction demandée
                x, y = x + dap * dd_i, y + dap * dd_j

            else:
                # virage impossible; conserver la direction courante
                return self.deplacer(self.direction, delta_t, plateau)

        else:
            # la direction demandée implique d'avancer ou de reculer
            x, y = x + dap * dd_i, y + dap * dd_j

            # calculer le gradient de l'acteur par rapport au centre de tuile
            dx, dy = x - i, y - j

            if (dx * dd_i + dy * dd_j > 0) and not plateau.tuile_franchissable(
                (i + dd_i, j + dd_j)
            ):
                # collision avec un obstacle; rebondir sur le centre de la tuile
                x, y = i, j

        # ajuster la nouvelle position de l'acteur
        self.position = plateau.normaliser_coordonnees((x, y))

        # et ajuster sa (potentiellement) nouvelle direction
        self.direction = direction

        return None
