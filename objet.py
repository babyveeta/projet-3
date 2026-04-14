"""Ce module contient la définition de la classe de base des objets du jeu Paxman."""


class Objet:
    """
    Un objet encapsule une position et une dimension sur le plateau de jeu.

    On suppose que les objets sont carrés.

    La position d'un objet correspond à son centre. Sa dimension correspond
    à sa largeur et sa hauteur.

    Les unités de position et de dimension des objets sont exprimés en tuiles de plateau.
    Par défaut, la dimension des objets est une tuile du plateau de jeu.
    """

    def __init__(self, x: float, y: float, *, dim: float = 1) -> None:
        """Construit une instance de la classe Objet, à partir de sa position
        (x, y) et de sa dimension dim."""

        # mémoriser la position de l'objet
        self.position = (x, y)

        # mémoriser sa dimension
        self.dimension = dim

    @property
    def position(self) -> tuple[float, float]:
        """Retourne la position de l'objet."""

        return self._pos

    @position.setter
    def position(self, pos: tuple[float, float]) -> None:
        """Définit la position de l'objet."""

        # valider la position
        if not (
            isinstance(pos, tuple)
            and len(pos) == 2
            and all(isinstance(x, (int, float)) for x in pos)
        ):
            raise TypeError("position invalide (doit être un tuple de 2 nombres)")

        # mémoriser la nouvelle position
        self._pos = pos

    @property
    def dimension(self) -> float:
        """Retourne la dimension de l'objet."""

        return self._dim

    @dimension.setter
    def dimension(self, dim: float) -> None:
        """Définit la dimension de l'objet."""

        # valider la dimension
        if not isinstance(dim, (int, float)):
            raise TypeError("dimension invalide (doit être un nombre > 0)")

        if dim <= 0:
            raise ValueError("dimension invalide (doit être un nombre > 0)")

        # mémoriser la nouvelle dimension
        self._dim = dim

    def calculer_distance_l1(self, pos: tuple[float, float]) -> float:
        """Retourne la distance de manhattan entre le centre de cet objet
        et une position arbitraire."""

        # obtenir le vecteur qui relie le centre de l'objet à la position spécifiée
        dx, dy = self.calculer_vecteur(pos)

        # retourner la norme L1 de ce vecteur
        return abs(dx) + abs(dy)

    def calculer_distance_l2(self, pos: tuple[float, float]) -> float:
        """Retourne la distance euclidienne entre le centre de cet objet
        et une position arbitraire."""

        # obtenir le vecteur qui relie le centre de l'objet à la position spécifiée
        dx, dy = self.calculer_vecteur(pos)

        # retourner la norme L2 de ce vecteur
        return (dx**2 + dy**2) ** 0.5

    def calculer_vecteur(self, pos: tuple[float, float]) -> tuple[float, float]:
        """Retourne le vecteur qui relie le centre de cet objet à une position arbitraire."""

        # extraire les coordonnées des objets
        x1, y1 = self.position
        x2, y2 = pos

        # retourner le vecteur qui relie les deux position
        return (x2 - x1, y2 - y1)
