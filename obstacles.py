"""Ce module contient les définitions des classes d'obstacles du jeu Paxman."""

from .objet import Objet


class Obstacle(Objet):
    """Un obstacle est un objet qui contraint le passage d'un acteur."""

    SORTES: set[str]

    def __init__(self, x: float, y: float, *, sorte: str):
        # initialiser la position de l'obstacle
        super().__init__(x, y)

        # valider la sorte d'obstacle
        if sorte not in self.SORTES:
            raise ValueError(f"la sorte d'obstacle doit être parmi {self.SORTES}")

        # mémoriser la sorte d'obstacle
        self._sorte = sorte


class Mur(Obstacle):
    """Un mur est un obstacle infranchissable."""

    # l'ensemble des symboles utilisés pour désigner les murs
    SORTES = set(["─", "│", "┌", "┐", "└", "┘"])


class Porte(Obstacle):
    """Une porte est un obstacle franchissable après un certain délai."""

    # l'ensemble des symboles utilisés pour désigner les portes
    SORTES = set(["_", ":"])

    @property
    def ouverture(self) -> bool:
        """Retourne l'état actuel d'ouverture de la porte."""

        return getattr(self, "_ouverture", False)

    @ouverture.setter
    def ouverture(self, valeur: bool) -> None:
        """Actualise l'état d'ouverture de la porte."""

        # mémoriser l'état d'ouverture de cette porte
        self._ouverture = valeur
