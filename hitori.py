import os
import sys
from datetime import datetime
from doctest import testmod
from math import floor
from tkinter import messagebox

from upemtk import *

CELL_SIZE = 50
PAGE_SIZE = 5
MARGIN = 20


# INFORMATIONS SUR LE PROGRAMME
#
# Le menu principal permet de charger un niveau par son nom,
# ou via une liste récupérée automatiquement à partir des
# fichiers dont l'extension est '.hti' (hitori file).
#
# Lors d'une partie, il est possible d'appuyer sur 'Echap' pour
# faire apparaitre le menu. De la il est alors possible de
# sauvegarder sa partie et de la continuer plus tard.
#

def pixel_to_cell(pixel: tuple):
    """
    Convertit les coordonées d'un pixel en coordonées d'une cellule du plateau.
    :param pixel: Coordonées du pixel.
    :return: Coordonées de la cellule.

    >>> pixel_to_cell((100, 200))
    (2, 4)
    """
    i, j = pixel
    return i // CELL_SIZE, j // CELL_SIZE


def format_time(time: int):
    """
    Formatte le temps sous la forme 'mm:ss' avec m pour les minutes et s pour les secondes.
    :param time: Temps à formater.
    :return: Temps formatté.

    >>> format_time(90)
    '01:30'
    """
    minutes = time // 60
    seconds = time % 60
    minutes = str(minutes) if minutes >= 10 else "0" + str(minutes)
    seconds = str(seconds) if seconds >= 10 else "0" + str(seconds)
    return minutes + ":" + seconds


def read_grid(file_name: str, blackened: set):
    """
    Décrit les valeurs de la grille contenue dans le fichier texte sous forme de liste de listes.
    La fonction renvoie une erreur si la grille est mal formée.
    :param file_name: Nom du fichier contenant la grille.
    :param blackened: Ensemble des cellules noircies.
    :return: Liste de listes décrivant la grille.

    >>> read_grid("grille.hti", set())
    [[2, 2, 1, 5, 3], [2, 3, 1, 4, 5], [1, 1, 1, 3, 5], [1, 3, 5, 4, 2], [5, 4, 3, 2, 1]]
    """
    # Ouverture du fichier.
    try:
        file = open(file_name, "r")
    except FileNotFoundError:
        messagebox.showerror("Erreur", "Fichier introuvable !")
        return
    grid = list()

    # Construction de la liste de listes.
    try:
        for i, line in enumerate(file):
            grid_line = list()
            for j, column in enumerate(line.strip().split()):
                if int(column) < 0:
                    blackened.add((i, j))
                grid_line.append(abs(int(column)))
            grid.append(grid_line)
    except ValueError:
        messagebox.showerror("Erreur", "La grille contient des valeurs inconnues !")
        return

    if not grid:
        messagebox.showerror("Erreur", "Le fichier est vide !")
        return

    # Vérification du format rectangulaire.
    if sum(len(line) for line in grid) != len(grid) * len(grid[0]):
        messagebox.showerror("Erreur", "La grille n'est pas rectangulaire !")
        return

    file.close()
    return grid


def display_grid(grid: list):
    """
    Affiche la grille dans la console.
    :param grid: Liste de listes décrivant la grille.

    >>> display_grid([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
    +---+---+---+
    | 1 | 2 | 3 |
    +---+---+---+
    | 4 | 5 | 6 |
    +---+---+---+
    | 7 | 8 | 9 |
    +---+---+---+
    """
    for line in grid:
        print(len(line) * "+---" + "+")
        for column in line:
            print("| {} ".format(column), end='')
        print("|")
    print(len(grid[0]) * "+---" + "+")


def write_grid(grid: list, blackened: set, file_name: str):
    """
    Écrit une grille sous forme de fichier texte.
    :param grid: Liste de listes décrivant la grille.
    :param blackened: Ensembles des cellules noircies.
    :param file_name: Nom du fichier de sortie.
    """
    file = open(file_name, "w")

    # Écriture de la grille.
    for i, line in enumerate(grid):
        for j, column in enumerate(line):
            if (i, j) in blackened:
                file.write(str(-column) + (" " if j + 1 < len(line) else "\n"))
            else:
                file.write(str(column) + (" " if j + 1 < len(line) else "\n"))

    file.close()


def without_conflict(grid: list, backened: set):
    """
    Vérifie que chaque numéro n'apparaisse qu'une fois par ligne et par colonne. (Règle n°1)
    :param grid: Liste de listes décrivant la grille.
    :param backened: Ensemble des cellules noircies.
    :return: Booléen déterminant s'il y a conflit.

    >>> without_conflict([[2, 2, 1, 5, 3], [2, 3, 1, 4, 5], [1, 1, 1, 3, 5], [1, 3, 5, 4, 2], [5, 4, 3, 2, 1]], \
                     {(2, 0), (0, 0), (3, 3), (2, 2), (3, 1), (0, 2), (1, 4)})
    True
    """
    # Vérification de l'unicité des nombres dans les lignes.
    for i, line in enumerate(grid):
        unique = list()
        for j, column in enumerate(line):
            if (i, j) in backened:
                continue
            if column not in unique:
                unique.append(column)
            else:
                return False

    # Vérification de l'unicité des nombres dans les colonnes.
    for j, column in enumerate([[line[column] for line in grid] for column in range(len(grid[0]))]):
        unique = list()
        for i, line in enumerate(column):
            if (i, j) in backened:
                continue
            if line not in unique:
                unique.append(line)
            else:
                return False

    return True


def without_adjacent(grid: list, blackened: set):
    """
    Vérifie qu'aucune cellule noircies ne soit adjacente à une autre. (Règle n°2)
    :param grid: Liste de listes décrivant la grille.
    :param blackened: Ensemble des cellules noircies.
    :return: Booléen déterminant s'il y a des cellules noircies voisines.

    >>> without_adjacent([[2, 2, 1, 5, 3], [2, 3, 1, 4, 5], [1, 1, 1, 3, 5], [1, 3, 5, 4, 2], [5, 4, 3, 2, 1]], \
                               {(2, 0), (0, 0), (3, 3), (2, 2), (3, 1), (0, 2), (1, 4)})
    True
    """
    # Parcours des cellules de la grille.
    for i, line in enumerate(grid):
        for j, column in enumerate(line):
            if (i, j) not in blackened:
                continue

            # Détermination de la présence d'une voisine.
            if i > 0 and (i - 1, j) in blackened:
                return False
            if i < len(grid) - 1 and (i + 1, j) in blackened:
                return False
            if j > 0 and (i, j - 1) in blackened:
                return False
            if j < len(grid[0]) - 1 and (i, j + 1) in blackened:
                return False

    return True


def related(grid: list, blackened: set):
    """
    Vérifie que la zone formée par toutes les cellules non noircies soit connexe. (Règle n°3)
    :param grid: Liste de listes décrivant la grille.
    :param blackened: Ensemble des cellules noircies.
    :return: Booléen déterminant si la zone non noircies est connexe.


    >>> related([[2, 2, 1, 5, 3], [2, 3, 1, 4, 5], [1, 1, 1, 3, 5], [1, 3, 5, 4, 2], [5, 4, 3, 2, 1]], \
                {(2, 0), (0, 0), (3, 3), (2, 2), (3, 1), (0, 2), (1, 4)})
    True
    """
    # Parcours des cellules de la grille.
    for i, line in enumerate(grid):
        for j, column in enumerate(line):
            if (i, j) in blackened:
                continue

            # Vérification de l'unicité de la zone formée en partant d'une cellule.
            return sum([len(line) for line in grid]) == len(blackened) + len(explore(grid, i, j, blackened))

    return False


def explore(grid: list, line: int, column: int, blackened: set, vacants: set = None):
    """
    Explore la grille afin de recupérer toutes les cellules libres en partant d'une cellule.
    :param grid: Liste de listes décrivant la grille.
    :param line: Ligne de la cellule actuelle.
    :param column: Colonne de la cellule actuelle.
    :param blackened: Ensemble des cellules noircies
    :param vacants: Ensemble des cellules libres.
    :return: Ensemble des cellules libres.
    """
    # Instanciation de l'ensemble des cellules libres.
    if vacants is None:
        vacants = set()

    # Vérification de l'état de la cellule.
    if (line, column) in blackened:
        return

    # Ajout de la cellule libre à l'ensemble.
    if (line, column) not in vacants:
        vacants.add((line, column))

    # Récursivité sur les cellules libres voisines.
    if line > 0 and (line - 1, column) not in blackened and (line - 1, column) not in vacants:
        explore(grid, line - 1, column, blackened, vacants)
    if line < len(grid) - 1 and (line + 1, column) not in blackened and (line + 1, column) not in vacants:
        explore(grid, line + 1, column, blackened, vacants)
    if column > 0 and (line, column - 1) not in blackened and (line, column - 1) not in vacants:
        explore(grid, line, column - 1, blackened, vacants)
    if column < len(grid[0]) - 1 and (line, column + 1) not in blackened and (line, column + 1) not in vacants:
        explore(grid, line, column + 1, blackened, vacants)

    return vacants


def draw_grid(grid: list, blackened: set):
    """
    Dessine la grille.
    :param grid: Liste de listes décrivant la grille.
    :param blackened: Ensemble des cellules noircies.
    """
    for i, line in enumerate(grid):
        for j, column in enumerate(line):
            # Dessin de la cellule.
            rectangle(MARGIN + j * CELL_SIZE,
                      MARGIN + i * CELL_SIZE,
                      MARGIN + j * CELL_SIZE + CELL_SIZE,
                      MARGIN + i * CELL_SIZE + CELL_SIZE,
                      remplissage="black" if (i, j) in blackened else "white")
            texte(MARGIN + j * CELL_SIZE + CELL_SIZE / 2,
                  MARGIN + i * CELL_SIZE + CELL_SIZE / 2,
                  column, ancrage="center", couleur="black" if (i, j) not in blackened else "white")


def contains_duplicates(lst: list, element: object):
    """
    Détecte si la liste contient des doublons
    :param lst: Liste.
    :param element: Élement dont il faut vérifier l'unicité.
    :return: Booléen du résultat.

    >>> contains_duplicates([1, 2, 3, 4], 1)
    False

    >>> contains_duplicates([1, 2, 3, 1], 1)
    True
    """
    unique = set()
    for e in lst:
        if e != element:
            continue
        if e not in unique:
            unique.add(e)
        else:
            return True
    return False


def solve(grid: list, blackened: set, duplicates: set, i: int = 0, j: int = 0):
    """
    Retourne l'ensemble des cellules noircies solution de la grille, ou None s'il n'y a aucune solution.
    :param grid: Liste de listes décrivant la grille.
    :param blackened: Ensemble des cellules noircies.
    :param duplicates: Ensemble des cellules en conflits.
    :param i: Indice de la ligne actuelle.
    :param j: Indice de la colonne actuelle.
    :return: Ensemble des cellules à noircir ou None si aucune solution n'existe.
    """

    # Définition d'une fonction permettant de passer en revue la cellule suivante.
    def next_cell():
        if j < len(grid[0]) - 1:
            return solve(grid, blackened, duplicates, i, j + 1)
        elif i < len(grid) - 1:
            return solve(grid, blackened, duplicates, i + 1, 0)
        else:
            return None

    if not without_adjacent(grid, blackened) or not related(grid, blackened):
        return None
    elif without_adjacent(grid, blackened) and related(grid, blackened) and without_conflict(grid, blackened):
        return blackened
    else:
        line = grid[i]
        column = [[line[column] for line in grid] for column in range(len(grid[0]))][j]

        if not contains_duplicates(line, grid[i][j]) and not contains_duplicates(column, grid[i][j]):
            return next_cell()
        else:
            blackened.add((i, j))
            if next_cell() is None:
                blackened.remove((i, j))
            return next_cell()


class Hitori:

    def __init__(self, file_name: str):
        # Initialisation du jeu
        cree_fenetre(0, 0)
        self.blackened = set()
        self.blackened_history = list()
        self.blackened_history_size = 0
        self.buttons = dict()
        self.victory = False
        self.pause = False

        # Initialisation de la grille.
        self.grid = read_grid(file_name, self.blackened)
        if self.grid is None:
            ferme_fenetre()
            return

        # Initialisation de la taille de la grille.
        self.GRID_HEIGHT = CELL_SIZE * len(self.grid)
        self.GRID_WIDTH = CELL_SIZE * len(self.grid[0])

        # Calcul des proportions relatives au texte.
        self.RIGHT_OFFSET = taille_texte('Noircies voisines')[0] - taille_texte('Noircies voisines')[0] % 5 + 20
        self.BAR_SIZE = taille_texte('X')[1] - taille_texte('X')[1] % 5 + 20

        # Calcul de la taille de la fenêtre.
        self.HEIGHT = self.GRID_HEIGHT + 2 * MARGIN + self.BAR_SIZE
        self.WIDTH = self.GRID_WIDTH + 2 * MARGIN + self.RIGHT_OFFSET
        ferme_fenetre()

        # Création des boutons.
        self.buttons["quit"] = Button("Quitter", lambda: sys.exit(0))
        self.buttons["cancel"] = Button("Annuler", lambda h=self: h.cancel())
        self.buttons["solve"] = Button("Résoudre", lambda h=self: h.solve())

        button_width = "Sauvegarder la partie"
        self.buttons["menu_pause"] = Button("Menu principal", lambda h=self: h.menu(), width=button_width)
        self.buttons["save_pause"] = Button("Sauvegarder la partie", lambda h=self: h.save(), width=button_width)
        self.buttons["quit_pause"] = Button("Quitter", lambda h=self: sys.exit(0), width=button_width)

        # Initialisation de la fenêtre principale.
        cree_fenetre(self.WIDTH, self.HEIGHT)

        # Boucle principale.
        while True:
            self.loop()

    def loop(self):
        """Boucle principale du jeu."""
        # Dessin des éléments.
        self.draw_elements()

        # Gestion des événements.
        while True:
            # Manipulation des événements.
            ev = donne_ev()
            if ev is not None:
                if type_ev(ev) == 'ClicGauche':
                    x, y = abscisse(ev), ordonnee(ev)
                    if not self.victory and not self.pause and \
                            MARGIN < x < MARGIN + self.GRID_WIDTH and MARGIN < y < MARGIN + self.GRID_HEIGHT:
                        y, x = pixel_to_cell((x - MARGIN, y - MARGIN))
                        self.blackened_history.append(self.blackened.copy())
                        if (x, y) in self.blackened:
                            self.blackened.discard((x, y))
                        else:
                            self.blackened.add((x, y))
                    else:
                        for button in self.buttons:
                            btn = self.buttons[button].get_coordinates()
                            if btn is None:
                                continue
                            if btn[0] <= x <= btn[2] and btn[1] <= y <= btn[3]:
                                self.buttons[button].execute()
                elif type_ev(ev) == 'Touche':
                    if touche(ev) == 'Escape':
                        self.pause = not self.pause
                elif type_ev(ev) == 'Quitte':
                    sys.exit(0)
                break
            mise_a_jour()

        # Nettoyage de la fenêtre.
        for btn in self.buttons.values():
            btn.reset()
        efface_tout()

    def draw_elements(self):
        """Dessine les éléments de l'interface."""
        draw_grid(self.grid, self.blackened)
        rectangle(0, self.HEIGHT - self.BAR_SIZE, self.WIDTH, self.HEIGHT, remplissage="black")

        # Affichage du message de victoire le cas échéant.
        if self.blackened_history_size < len(self.blackened_history):
            self.blackened_history_size = len(self.blackened_history)
            if without_conflict(self.grid, self.blackened) and without_adjacent(self.grid, self.blackened) and \
                    related(self.grid, self.blackened):
                texte(10, self.BAR_SIZE / 2 + 2 * MARGIN + self.GRID_HEIGHT, "Gagné !", ancrage="w", couleur="green")
                self.victory = True

        # Dessin des indications d'aide à la résolution.
        i = 0
        texte(2 * MARGIN + self.GRID_WIDTH, MARGIN + CELL_SIZE / 2 + i * CELL_SIZE, "Conflits", ancrage="w",
              couleur="green" if without_conflict(self.grid, self.blackened) else "red")
        i += 1
        texte(2 * MARGIN + self.GRID_WIDTH, MARGIN + CELL_SIZE / 2 + i * CELL_SIZE, "Noires voisines", ancrage="w",
              couleur="green" if without_adjacent(self.grid, self.blackened) else "red")
        i += 1
        texte(2 * MARGIN + self.GRID_WIDTH, MARGIN + CELL_SIZE / 2 + i * CELL_SIZE, "Connexe", ancrage="w",
              couleur="green" if related(self.grid, self.blackened) else "red")

        if self.pause:
            rectangle(0, 0, self.WIDTH, self.HEIGHT, remplissage="black", couleur="black")
            texte(self.WIDTH / 2, CELL_SIZE, "Menu", ancrage='n', taille=32, couleur="white")
            for i, (value, button) in enumerate(self.buttons.items()):
                if "pause" not in value:
                    continue
                button.draw(self.WIDTH / 2, i * CELL_SIZE, "center")
        else:
            # Dessin des boutons de jeu
            last_button = None
            for value, button in self.buttons.items():
                # Conditions
                if "pause" in value:
                    continue
                if value == "cancel" and not self.blackened_history:
                    continue
                if value == "solve" and self.victory:
                    continue

                if last_button is None:
                    button.draw(self.WIDTH - 5, self.HEIGHT - 5, "se")
                else:
                    button.draw(last_button.get_coordinates()[0] - 5, self.HEIGHT - 5, "se")
                last_button = button

    def cancel(self):
        """Annule le dernier coup."""
        self.blackened = self.blackened_history[-1]
        self.blackened_history.pop()
        if self.victory:
            self.victory = False
        self.blackened_history_size -= 1

    def solve(self):
        """Résout la grille actuelle."""
        self.blackened_history.append(self.blackened.copy())

        duplicates = set()
        solution = solve(self.grid, set(), duplicates)

        if solution is not None:
            self.blackened = solution

    def save(self):
        """Sauvegarde la partie."""
        file_name = datetime.now().strftime("%d-%m-%Y %H-%M") + ".hti"
        write_grid(self.grid, self.blackened, file_name)
        messagebox.showinfo("Succès", "La partie a été sauvegardée dans le fichier " + file_name + ".")
        self.pause = False

    @staticmethod
    def menu():
        """Ferme la partie et lance le menu principal."""
        ferme_fenetre()
        Menu()


class Menu:

    def __init__(self):
        self.WIDTH = 7 * CELL_SIZE
        self.HEIGHT = 7 * CELL_SIZE
        self.buttons = dict()

        button_width = "X" * 15
        self.buttons["game_list"] = Button("Liste des grilles", lambda m=self: m.grid_list(), width=button_width)
        self.buttons["load_game"] = Button("Charger une grille", lambda m=self: m.load(), width=button_width)
        self.buttons["quit"] = Button("Quitter", lambda: sys.exit(0), width=button_width)

        cree_fenetre(self.WIDTH, self.HEIGHT)

        while True:
            self.loop()

    def loop(self):
        """Boucle du menu."""
        # Dessin des éléments.
        texte(self.WIDTH / 2, CELL_SIZE, "HITORI", taille=48, ancrage='n')

        for i, (value, button) in enumerate(self.buttons.items()):
            button.draw(self.WIDTH / 2, ((i + 4) if value == "quit" else (i + 3)) * CELL_SIZE, anchor='n', fill="black",
                        color="white")

        # Manipulation des événements.
        while True:
            ev = donne_ev()
            if ev is not None:
                if type_ev(ev) == 'ClicGauche':
                    x, y = abscisse(ev), ordonnee(ev)
                    for button in self.buttons:
                        btn = self.buttons[button].get_coordinates()
                        if btn is None:
                            continue
                        if btn[0] <= x <= btn[2] and btn[1] <= y <= btn[3]:
                            self.buttons[button].execute()
                elif type_ev(ev) == 'Touche':
                    pass
                elif type_ev(ev) == 'Quitte':
                    sys.exit(0)
                break

            mise_a_jour()

        # Réinitialisation des boutons.
        for btn in self.buttons.values():
            btn.reset()

        # Nettoyage de la fenêtre.
        efface_tout()

    @staticmethod
    def load():
        """Ferme le menu et charge une grille."""
        messagebox.showinfo("Information", "Veuillez entrer le nom du fichier dans la console.")
        file_name = input("Nom du fichier : ")
        ferme_fenetre()
        Hitori(file_name)

    @staticmethod
    def grid_list():
        """Ferme le menu et ouvre le sélecteur de grilles."""
        ferme_fenetre()
        GameList()


class GameList:

    def __init__(self):
        self.WIDTH = 9 * CELL_SIZE
        self.HEIGHT = floor(7.5 * CELL_SIZE)
        self.buttons = dict()
        self.grid_files = list()

        self.buttons["next"] = Button(">", lambda gl=self: gl.next(), height="X" * 10)
        self.buttons["prev"] = Button("<", lambda gl=self: gl.prev(), height="X" * 10)
        self.buttons["back"] = Button("←", lambda gl=self: gl.back(), height="_°")

        # Récupération des fichiers en '.hti'.
        for file in sorted(os.listdir(os.curdir)):
            if file.split(".")[-1] != "hti":
                continue
            self.grid_files.append(file)
            self.buttons[file] = Button(file, lambda gl=self, f=file: gl.load(f), width="X" * 16)

        self.page = 0
        self.max_page = len(self.grid_files) // PAGE_SIZE

        cree_fenetre(self.WIDTH, self.HEIGHT)
        while True:
            self.loop()

    def loop(self):
        # Dessin des éléments.
        self.draw_elements()

        # Manipulation des événements.
        while True:
            ev = donne_ev()
            if ev is not None:
                if type_ev(ev) == 'ClicGauche':
                    x, y = abscisse(ev), ordonnee(ev)
                    for button in self.buttons:
                        btn = self.buttons[button].get_coordinates()
                        if btn is None:
                            continue
                        if btn[0] <= x <= btn[2] and btn[1] <= y <= btn[3]:
                            self.buttons[button].execute()
                elif type_ev(ev) == 'Touche':
                    pass
                elif type_ev(ev) == 'Quitte':
                    sys.exit(0)
                break

            mise_a_jour()

        # Réinitialisation des boutons.
        for btn in self.buttons.values():
            btn.reset()

        # Nettoyage de la fenêtre.
        efface_tout()

    def draw_elements(self):
        """Dessine les éléments de l'interface."""
        texte(self.WIDTH / 2, CELL_SIZE / 2, "Liste des grilles", taille=30, ancrage='n')

        texte(self.WIDTH / 2, self.HEIGHT - 10, "Page {} sur {}".format(str(self.page + 1), str(self.max_page + 1)),
              ancrage='s')

        if self.max_page > 0:
            if self.page > 0:
                self.buttons["prev"].draw(10, self.HEIGHT // 2 + CELL_SIZE // 2, anchor="w", fill="black",
                                          color="white")
            if self.page < self.max_page:
                self.buttons["next"].draw(self.WIDTH - 10, self.HEIGHT // 2 + CELL_SIZE // 2, anchor="e", fill="black",
                                          color="white")
        self.buttons["back"].draw(10, 10)

        for i, file in enumerate(self.grid_files):
            if self.page * PAGE_SIZE <= i < (self.page + 1) * PAGE_SIZE:
                self.buttons[file].draw(self.WIDTH // 2, (i % PAGE_SIZE + 2) * CELL_SIZE, anchor='center')

    @staticmethod
    def back():
        """Ferme la liste des grilles et ouvre le menu principal."""
        ferme_fenetre()
        Menu()

    def prev(self):
        """Passe à la page précédente."""
        if self.page > 0:
            self.page -= 1

    def next(self):
        """Passe à la page suivante."""
        if self.page < self.max_page:
            self.page += 1

    @staticmethod
    def load(file_name):
        """Ferme le selecteur de grille et ouvre le niveau."""
        ferme_fenetre()
        Hitori(file_name)


class Button:

    def __init__(self, content: str, action: callable, width: str = None, height: str = None):
        """Créer un bouton."""
        self.content = content
        self.action = action
        self.coordinates = None
        self.width = width
        self.height = height

    def draw(self, x: int, y: int, anchor: str = 'nw', fill: str = 'white', color: str = 'black', size: int = 24):
        """Dessine le bouton et stocke ses coordonées."""
        # Calcul et arrondissement des dimensions.
        if self.width is None:
            width = taille_texte(self.content, taille=size)[0]
        else:
            width = taille_texte(self.width, taille=size)[0]

        if self.height is None:
            height = taille_texte(self.content, taille=size)[1]
        else:
            height = taille_texte(self.height, taille=size)[0]
        height -= height % 5

        # Dessin du bouton en fonction de son ancrage.
        if anchor == 'nw':
            rectangle(x, y, x + width + 2 * 5, y + height + 2 * 5, remplissage=fill)
            texte(x + (width + 2 * 5) // 2, y + (height + 2 * 5) // 2, self.content, ancrage='center', taille=size,
                  couleur=color)
            self.coordinates = x, y, x + width + 2 * 5, y + height + 2 * 5
        elif anchor == 'n':
            rectangle(x - (width + 2 * 5) // 2, y, x + (width + 2 * 5) // 2, y + height + 2 * 5,
                      remplissage=fill)
            texte(x, y + (height + 2 * 5) // 2, self.content, ancrage='center', taille=size, couleur=color)
            self.coordinates = x - (width + 2 * 5) // 2, y, x + (width + 2 * 5) // 2, y + height + 2 * 5
        elif anchor == 'ne':
            rectangle(x - width - 2 * 5, y, x, y + height + 2 * 5, remplissage=fill)
            texte(x + (width + 2 * 5) // 2, y - (height + 2 * 5) // 2, self.content, ancrage='center', taille=size,
                  couleur=color)
            self.coordinates = x - width - 2 * 5, y, x, y + height + 2 * 5
        elif anchor == 'e':
            rectangle(x - width - 2 * 5, y - (height + 2 * 5) // 2, x, y + (height + 2 * 5) // 2, remplissage=fill)
            texte(x - (width + 2 * 5) // 2, y, self.content, ancrage='center', taille=size, couleur=color)
            self.coordinates = x - height - 2 * 5, y - (height + 2 * 5) // 2, x, y + (height + 2 * 5) // 2
        elif anchor == 'se':
            rectangle(x - width - 2 * 5, y - height - 2 * 5, x, y, remplissage=fill)
            texte(x - (width + 2 * 5) // 2, y - (height + 2 * 5) // 2, self.content, ancrage='center', taille=size,
                  couleur=color)
            self.coordinates = x - width - 2 * 5, y - height - 2 * 5, x, y
        elif anchor == 's':
            rectangle(x - (width + 2 * 5) // 2, y - height - 2 * 5, x + (width + 2 * 5) // 2, y, remplissage=fill)
            texte(x, y - (height + 2 * 5) // 2, self.content, ancrage='center', taille=size, couleur=color)
            self.coordinates = x - (width + 2 * 5) // 2, y - height - 2 * 5, x + (width + 2 * 5) // 2, y
        elif anchor == 'sw':
            rectangle(x, y - height - 2 * 5, x + width + 2 * 5, y, remplissage=fill)
            texte(x + (width + 2 * 5) // 2, y - (height + 2 * 5) // 2, self.content, ancrage='center', taille=size,
                  couleur=color)
            self.coordinates = x, y - height - 2 * 5, x + width + 2 * 5, y
        elif anchor == 'w':
            rectangle(x, y - (height + 2 * 5) // 2, x + width + 2 * 5, y + (height + 2 * 5) // 2, remplissage=fill)
            texte(x + (width + 2 * 5) // 2, y, self.content, ancrage='center', taille=size, couleur=color)
            self.coordinates = x, y - (height + 2 * 5) // 2, x + height + 2 * 5, y + (height + 2 * 5) // 2
        elif anchor == 'center':
            rectangle(x - (width + 2 * 5) // 2, y - (height + 2 * 5) // 2, x + (width + 2 * 5) // 2,
                      y + (height + 2 * 5) // 2, remplissage=fill)
            texte(x, y, self.content, ancrage='center', taille=size, couleur=color)
            self.coordinates = x - (width + 2 * 5) // 2, y - (height + 2 * 5) // 2, x + (
                    width + 2 * 5) // 2, y + (height + 2 * 5) // 2

    def get_coordinates(self):
        """
        Retourne les coordonnées du rectangle du bouton.
        :return: Coordonnées du rectangle.
        """
        return self.coordinates

    def execute(self):
        """
        Déclenche la fonction associée au bouton.
        """
        if self.action is not None:
            self.action()

    def reset(self):
        """Réinitialise le bouton."""
        self.coordinates = None


if __name__ == "__main__":
    testmod()
    Menu()
