"""Ce module contient les définitions des classes de récompenses du jeu Paxman."""

from .objet import Objet


class Recompense(Objet):
    """Une récompense est un objet qu'un acteur peut recueillir au passage
    et qui lui accorde des points.
    """

    def __init__(self, x: float, y: float, *, pts: int, dim: float = 0.8) -> None:
        # initialiser la position et la dimension de la récompense
        super().__init__(x, y, dim=dim)

        if not isinstance(pts, int):
            raise ValueError("une récompense doit être un nombre entier")

        # mémoriser son nombre de points
        self._pts = pts

    @property
    def points(self) -> int:
        """Retourne la valeur de la récompense."""

        return self._pts


class Pilule(Recompense):
    """Une pilule est une récompense qui vaut 10 points."""

    def __init__(self, x: float, y: float, *, pts: int = 10, dim: float = 0.25) -> None:
        # initialiser cette récompense
        super().__init__(x, y, dim=dim, pts=pts)


class PiluleForce(Pilule):
    """Une pilule de force est une récompense qui vaut 100 points.

    Lorsque Paxman avale une pilule de force, non seulement il gagne des points de
    récompense, mais il apeure aussi les fantômes en les rendant vulnérables.
    Ceux-ci vont tous se mettre à fuir Paxman pendant un certain nombre de secondes.
    Durant ce temps, Paxman pourra les tuer s'il se retrouve sur la même tuile de jeu qu'eux.
    """

    def __init__(self, x: float, y: float, *, pts: int = 100, dim: float = 0.75) -> None:
        # initialiser cette récompense
        super().__init__(x, y, dim=dim, pts=pts)
