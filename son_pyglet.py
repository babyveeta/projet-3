"""Gestion des sons avec pyglet pour le jeu Paxman."""

from enum import Enum
from typing import Self

import pyglet


class Son(Enum):
    """Enumération des fichiers de sons utilisés par le jeu Paxman."""

    SIRENE = "sons/siren.wav"
    MANGE_PILULE = "sons/eat_dot.wav"
    MANGE_FANTOME = "sons/eat_ghost.wav"
    PAXMAN_REQUIEM = "sons/death.wav"
    FANTOMES_ENFUITE = "sons/fright.wav"


class LecteurSon(pyglet.media.Player):
    """Classe qui encapsule les sons du jeu."""

    def __init__(self, son: Son, *, en_boucle: bool = False, volume: float = 1.0) -> None:
        """Initialise un son à partir d'un fichier."""
        super().__init__()

        if not isinstance(son, Son):
            raise TypeError("Le paramètre 'son' doit être une instance de Son")

        if en_boucle:
            # activer la lecture en boucle
            self.loop = True

        # ajuster le volume du son
        self.volume = volume

        # charger le son à partir du fichier
        self._son = pyglet.media.load(son.value)
        self._son = pyglet.media.load(son.value, streaming=False)

    def jouer(self) -> Self:
        """Joue le son."""

        # ajouter la source au lecteur
        self.queue(self._son)

        # démarrer ou redémarrer la lecture du son
        self.play()

        # retourner le son qui joue pour permettre de faire du chaînage de méthodes
        return self

    def arreter(self) -> None:
        """Arrête le son."""

        # arrêter la lecture du son
        self.pause()
