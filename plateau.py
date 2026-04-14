"""Ce module contient la définition de la classe qui encapsule le plateau de jeu."""

from .objet import Objet
from .obstacles import Mur, Obstacle, Porte
from .recompenses import Pilule, PiluleForce


class Plateau(dict[tuple[float, float], Objet]):
    """Un plateau de jeu est une grille de tuiles contenant des objets."""

    def __init__(self, description: list[str] | None) -> None:
        # initialiser les dimensions du plateau
        self._dim = None

        if description is not None:
            # construire le plateau à partir de sa description
            self.reinitialiser(description)

            # construire son graphe de connexité
            # self._construire_graphe()

    @property
    def largeur(self) -> int:
        """retourne la largeur du plateau (en unités de tuile)."""
        if self._dim is None:
            raise RuntimeError("le plateau n'a pas encore été initialisé")

        return self._dim[0]

    @property
    def hauteur(self) -> int:
        """Retourne la hauteur du plateau (en unités de tuile)."""
        if self._dim is None:
            raise RuntimeError("le plateau n'a pas encore été initialisé")

        return self._dim[1]

    @property
    def obstacles(self) -> list[Objet]:
        """Retourne un itérable des obstacles du plateau."""

        return filter(lambda obj: isinstance(obj, Obstacle), self.values())

    @property
    def recompenses(self) -> list[Objet]:
        """Retourne un itérable des récompenses du plateau."""

        return filter(lambda obj: isinstance(obj, (Pilule, PiluleForce)), self.values())

    def tuile_franchissable(self, pos: tuple[float, float]) -> bool:
        """Détermine si la tuile sous-jacente à cette position est franchissable."""

        # obtenir les coordonnées normalisées du centre de la tuile
        i, j = self.normaliser_coordonnees((round(pos[0]), round(pos[1])))

        # obtenir l'objet sous-jacent du plateau
        obj = self.get((i, j))

        match obj:
            case Mur():
                # les murs ne sont jamais franchissables
                return False

            case Porte():
                # les portes fermées ne sont jamais franchissables
                if obj.ouverture is False:
                    return False

        # tout le reste est franchissable
        return True

    def normaliser_coordonnees(self, pos: tuple[float, float]) -> tuple[float, float]:
        """Retourne la position reçue, mais avec ses coordonnées normalisées."""

        # lier les extrémités des lignes et des colonnes du plateau
        return (((pos[0] - 1) % self.largeur) + 1, ((pos[1] - 1) % self.hauteur) + 1)

    def reinitialiser(self, description: list[str]) -> None:
        """Réinitialise le plateau à partir de sa description textuelle."""

        # valide la description textuelle
        self._dim = self._valider(description)

        # vider les éléments du plateau
        self.clear()

        # traiter toutes les lignes du plateau
        for j, ligne in enumerate(description):
            # inverser l'axe des ordonnées pour que l'origine soit en bas à gauche
            j = self.hauteur - j

            # traiter toutes les colonnes du plateau
            for i, symbole in enumerate(ligne, 1):
                if symbole in ["─", "│", "┌", "┐", "└", "┘"]:
                    # cas d'un mur
                    self[(i, j)] = Mur(x=i, y=j, sorte=symbole)

                elif symbole in ["_", ":"]:
                    # cas d'une porte
                    self[(i, j)] = Porte(x=i, y=j, sorte=symbole)

                elif symbole == ".":
                    # cas d'une pilule
                    self[(i, j)] = Pilule(x=i, y=j)

                elif symbole == "o":
                    # cas d'une pilule d'invincibilité
                    self[(i, j)] = PiluleForce(x=i, y=j)

    def _valider(self, description: list[str]) -> tuple[int, int]:
        """Valide la description textuelle du plateau."""

        # déterminer le nombre de tuiles verticales
        dim_y = len(description)

        # déterminer le nombre de tuiles horizontales
        dim_x = len(description[0])

        # vérifier que toutes les lignes de la description sont de la même longueur
        for ligne in description:
            if len(ligne) != dim_x:
                raise RuntimeError(
                    "description invalide; les lignes doivent toutes être de même longueur"
                )

        # retourner le tuple des dimension du plateau (largeur, hauteur)
        return (dim_x, dim_y)
