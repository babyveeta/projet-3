"""Ce module contient la définition de la classe qui encapsule le paxman."""

from __future__ import annotations
import random
from .acteur import Acteur
from .recompenses import PiluleForce

class Paxman(Acteur):
    """Un paxman est l'acteur principal du jeu."""

    def __init__(self, x: int, y: int, *, reglages: dict[str, str | float]) -> None:
        # initialiser la position de Paxman
        super().__init__(x, y)

        # mémoriser ses réglages
        self._reglages = reglages

        # initialiser sa vitesse
        self.vitesse = self.reglage("vitesse-défaut")

        # initialiser son score
        self.score = 0

    @property
    def score(self) -> int:
        """Retourne le score actuel de Paxman."""

        return self._score

    @score.setter
    def score(self, valeur: int) -> None:
        """Définit le score de Paxman."""

        # valider la valeur
        if not isinstance(valeur, int):
            raise TypeError("le score doit être un entier")

        if valeur < 0:
            raise ValueError("Le score doit être supérieur ou égal à zéro")

        # mémoriser le nouveau score
        self._score = valeur


    def choisir_une_direction(self, jeu):
        """Choisit la direction optimale pour Paxman."""
        i, j = self.tuile_courante()

        directions = [(0,1), (0,-1), (1,0), (-1,0)]
        directions_valides = [
            (dx, dy) for dx, dy in directions
            if jeu.plateau.tuile_franchissable((i+dx, j+dy))
        ]

        if not directions_valides:
            return (0, 0)

        # Éviter demi-tour
        anti_retour = (-self.direction[0], -self.direction[1])
        directions_filtrees = [d for d in directions_valides if d != anti_retour]
        directions_valides = directions_filtrees or directions_valides

        def direction_vers(cible):
            return min(
                directions_valides,
                key=lambda d: abs((i+d[0]) - cible[0]) + abs((j+d[1]) - cible[1])
            )

        # =========================================
        # 1. PILULE FORCE (PRIORITÉ ABSOLUE)
        # =========================================
        cible_force = min(
            (obj for obj in jeu.plateau.recompenses if isinstance(obj, PiluleForce)),
            key=lambda obj: self.calculer_distance_l1(obj.position),
            default=None
        )

        if cible_force is not None:
            return direction_vers(cible_force.position)

        # =========================================
        # 2. CHASSE (fantôme en fuite accessible)
        # =========================================
        if jeu.timer_fuite > 2:
            cible_fantome = min(
                (f for f in jeu.fantomes.values() if f.mode == "fuite"),
                key=lambda f: self.calculer_distance_l1(f.position),
                default=None
            )
            if cible_fantome is not None:
                return direction_vers(cible_fantome.position)

    # =========================================
    # 3. FUITE / SURVIE
    # =========================================
        def distance_fantome_min(d):
            nx, ny = i + d[0], j + d[1]
            return min(
                abs(nx - f.position[0]) + abs(ny - f.position[1])
                for f in jeu.fantomes.values()
            )

        meilleures = sorted(directions_valides, key=distance_fantome_min, reverse=True)
        return random.choice(meilleures[:2])
