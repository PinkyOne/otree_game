import math
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
    players_per_group = 3
    num_rounds = 4

    instructions_template = 'cournot/Instructions.html'

    base_points = 50
    # Total production capacity of all players
    total_capacity = 60

    b = 2000


class Subsession(BaseSubsession):
    def get_R(self):
        return self.session.config['R']


class Group(BaseGroup):
    price = models.CurrencyField(
        doc="""Unit price: P = T - \sum U_i, where T is total capacity and U_i is the number of units produced by player i"""
    )
    total_units = models.PositiveIntegerField(
        doc="""Total units produced by all players"""
    )
    a = None

    def get_a(self):
        if (self.a is None):
            a_strings = self.session.config['a'].replace(" ","").split(',')
            a = []
            for a_i in a_strings:
                a.append(int(a_i))

            self.a = a
        return self.a

    def get_R(self):
        return self.session.config['R']

    def set_payoffs(self):
        Bank.make_decision(self)


class Player(BasePlayer):
    units = models.PositiveIntegerField(
        min=0, max=None,
        doc="""Размер заявки"""
    )
    fitness_function = None

    def get_target_payoff(self):
        return Constants.b / (2 * self.get_a_i())

    def get_fitness_function(self):
        if self.fitness_function is None:
            a = self.get_a_i()
            self.fitness_function = lambda x: Constants.b * x - a * x * x
        print(self.fitness_function)
        return self.fitness_function

    def get_a_i(self):
        a = self.group.get_a()
        return a[self.id_in_group - 1]

    def other_player(self):
        return self.get_others_in_group()[0]

    def get_fitness_function_value(self):
        return c(self.get_fitness_function()(self.payoff))


class Bank():
    @staticmethod
    def make_decision(group):
        players = group.get_players()
        sum = 0
        for player in players:
            sum += player.get_target_payoff() / player.units
        for player in players:
            x = player.get_target_payoff() / player.units
            player.payoff = (x * group.get_R()) / sum

    @staticmethod
    def make_decision_old(group):
        players = group.get_players()
        pool = Bank.divide_resources(players)
        Bank.divide_remained_resources(pool, players)

    @staticmethod
    def divide_resources(players):
        sorted_players_list = sorted(players, key=lambda player: player.units)
        players_count = len(sorted_players_list)
        pool = Constants.R
        avg = int(round(pool / players_count))
        for player in sorted_players_list:
            if player.units <= avg:
                player.payoff = player.units
            else:
                player.payoff = avg
            pool -= player.payoff
            players_count -= 1
            if players_count > 0:
                avg = int(round(pool / players_count))
        return pool

    @staticmethod
    def divide_remained_resources(pool, players):
        if pool > 0:
            avg = int(round(pool / len(players)))
            for player in players:
                player.payoff += avg
