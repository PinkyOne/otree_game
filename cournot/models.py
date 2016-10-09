from otree.api import (
    models, widgets, BaseConstants, BaseSubsession, BaseGroup, BasePlayer,
    Currency as c, currency_range
)
import random
from random import randint

doc = """
In Cournot competition, firms simultaneously decide the units of products to
manufacture. The unit selling price depends on the total units produced. In
this implementation, there are 2 firms competing for 1 period.
"""


class Constants(BaseConstants):
    name_in_url = 'cournot'
    players_per_group = 2
    num_rounds = 5

    instructions_template = 'cournot/Instructions.html'

    base_points = 50
    # Total production capacity of all players
    total_capacity = 60
    max_units_per_player = int(total_capacity / players_per_group)


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    R = 1000
    p = 2000
    pR = p * R

    price = models.CurrencyField(
        doc="""Unit price: P = T - \sum U_i, where T is total capacity and U_i is the number of units produced by player i"""
    )

    total_units = models.PositiveIntegerField(
        doc="""Total units produced by all players"""
    )

    def get_pR(self):
        return self.pR

    def set_payoffs(self):
        self.total_units = sum([p.units for p in self.get_players()])
        self.price = Constants.total_capacity - self.total_units
        for p in self.get_players():
            p.payoff = self.price * p.units


class Player(BasePlayer):
    FITNESS_FUNCTIONS = [
        dict(function=lambda x: x * x, func_to_string="x^2"),
        dict(function=lambda x: x * x * 2, func_to_string="2 * x^2"),
        dict(function=lambda x: x * x * x * x / 50, func_to_string="x^4 / 50"),
        dict(function=lambda x: x * x * x * x / 100, func_to_string="x^4 / 100")
    ]

    fitness_function = None

    units = models.PositiveIntegerField(
        min=0, max=Constants.max_units_per_player,
        doc="""Quantity of units to produce"""
    )

    def get_fitness_function(self):
        if self.fitness_function is None:
            rand_int = randint(0, len(Player.FITNESS_FUNCTIONS) - 1)
            self.fitness_function = Player.FITNESS_FUNCTIONS[rand_int]
            Player.FITNESS_FUNCTIONS.remove(self.fitness_function)

        return self.fitness_function.get('func_to_string')

    def other_player(self):
        return self.get_others_in_group()[0]

    def get_fitness_function_value(self, x):
        return Group.pR - self.fitness_function.get('func_to_string')(x)
