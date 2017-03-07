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
    name_in_url = 'cournot_with_korgin_calc'
    players_per_group = 3
    num_rounds = 10
    rounds = range(1, num_rounds + 1)
    rules = range(1, 6)

    instructions_template = 'cournot_with_korgin_calc/Instructions.html'
    korgin_calculator_template = 'cournot_with_korgin_calc/Korgin_calculator.html'
    chart_template = 'cournot_with_korgin_calc/Previous_round_chart.html'
    table_with_results_template = 'cournot_with_korgin_calc/Table_with_results.html'
    fuzzy_promter = 'cournot_with_korgin_calc/Fuzzy_promter.html'

    base_points = 50
    # Total production capacity of all players
    total_capacity = 60


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

    def get_requests(self):
        requests = []
        for player in self.get_players():
            requests.append(int(player.in_round(player.round_number - 1).units))
        return requests

    def get_payoffs(self):
        payoffs = []
        for player in self.get_players():
            payoffs.append(player.in_round(player.round_number - 1).payoff)
        return payoffs

    def get_target_payoffs(self):
        payoffs = []
        for player in self.get_players():
            payoffs.append(player.in_round(player.round_number - 1).get_target_payoff())
        return payoffs

    def get_a(self):
        if self.a is None:
            a_strings = self.session.config['a'].replace(" ", "").split(',')
            a = []
            for a_i in a_strings:
                a.append(float(a_i))

            self.a = a
        return self.a

    def get_R(self):
        return self.session.config['R']

    def get_b(self):
        return self.session.config['b']

    def set_payoffs(self):
        Bank.make_decision(self)


class Player(BasePlayer):
    units = models.PositiveIntegerField(
        min=1, max=None,
        doc="""Размер заявки"""
    )
    fake_a = models.FloatField(
        min=0.00000000000000000000001, max=1000.0, blank=True,
        doc="""Значение параметра a целевой функции"""
    )
    fitness_function = None
    previous_units = None


    def get_with_korgin(self):
        with_random_promter = 'true' in self.session.config['with_random_promter']
        with_korgin = 'true' in self.session.config['with_korgin']
        if with_random_promter:
            with_korgin = self.id_in_group == 1
        print(self.id_in_group)
        return with_korgin

    def get_with_fuzzy_promter(self):
        with_random_promter = 'true' in self.session.config['with_random_promter']
        with_fuzzy_promter = 'true' in self.session.config['with_fuzzy_promter']
        if with_random_promter:
            with_fuzzy_promter = self.id_in_group == 3
        print(self.id_in_group)
        return with_fuzzy_promter

    def get_units(self):
        return c(self.units)

    def get_korgin_value(self):
        return KorginPromter.calculate_korgin_value(self.group, self)

    def get_target_payoff(self):
        if self.fake_a is None:
            a = self.get_a_i()
        else:
            a = self.fake_a
        return int(self.group.get_b() / (2 * a))

    def get_real_target_payoff(self):
        a = self.get_a_i()
        return int(self.group.get_b() / (2 * a))

    def get_target_fitness_function_value(self):
        return self.get_fitness_function()(self.get_real_target_payoff())

    def get_fitness_function(self):
        if self.fitness_function is None:
            a = self.get_a_i()
            self.fitness_function = lambda x: self.group.get_b() * x - a * x * x
        print(self.fitness_function)
        return self.fitness_function

    def get_a_i(self):
        a = self.group.get_a()
        return a[self.id_in_group - 1]

    def other_player(self):
        return self.get_others_in_group()[0]

    def get_fitness_function_value(self):
        return c(self.get_fitness_function()(self.payoff))

    def get_fuzzy_tip(self):
        return FuzzyPromter.get_tip_values(self)


class FuzzyPromter():
    @staticmethod
    def get_n(group):
        n = 0.0
        for player in group.get_players():
            print(player.id_in_group)
            print(FuzzyPromter.get_alpha(player))
            if FuzzyPromter.get_alpha(player) >= 1.0:
                n += 1.0
        return n / len(group.get_players())

    @staticmethod
    def get_alpha(player):
        payoff = int(player.in_round(player.round_number - 1).payoff)
        target_payoff = player.get_real_target_payoff()
        return payoff / target_payoff

    @staticmethod
    def get_mu_alphas(player):
        alpha = FuzzyPromter.get_alpha(player)
        print("alpha: "+str(alpha))
        mu_alphas = {}

        mu_alphas['low'] = 1.0 - alpha if alpha <= 1.0 else 0.0

        if 0 < alpha <= 0.5:
            mu_alphas['near1'] = 0.0
        elif 0.5 < alpha <= 1.0:
            mu_alphas['near1'] = 2 * alpha - 1.0
        elif 1.0 < alpha <= 1.5:
            mu_alphas['near1'] = 3.0 - 2 * alpha
        else:
            mu_alphas['near1'] = 0

        target_payoff = player.get_real_target_payoff()
        r = player.group.get_R()
        x_div_r = target_payoff / r

        mu_alphas['high'] = 0.0 if alpha <= 1.0 else x_div_r * alpha - x_div_r
        return mu_alphas

    @staticmethod
    def defuzz_alpha(player):
        mu_alphas = FuzzyPromter.get_mu_alphas(player)
        inverse = [(value, key) for key, value in mu_alphas.items()]
        pair = Pair()
        pair.set_key_value(max(inverse)[1], mu_alphas[max(inverse)[1]])
        return pair

    @staticmethod
    def defuzz_n(player):
        mu_n = FuzzyPromter.get_mu_n(player)
        inverse = [(value, key) for key, value in mu_n.items()]
        pair = Pair()
        pair.set_key_value(max(inverse)[1], mu_n[max(inverse)[1]])
        return pair

    @staticmethod
    def get_mu_n(player):
        mu_n = {}
        mu_n['low'] = 1 - FuzzyPromter.get_n(player.group)
        mu_n['high'] = FuzzyPromter.get_n(player.group)
        return mu_n

    @staticmethod
    def get_tip(player):
        mu_n = FuzzyPromter.get_mu_n(player)
        mu_alpha = FuzzyPromter.get_mu_alphas(player)
        print(mu_n)
        print(mu_alpha)
        rules = []
        max_id = 0
        max = min(mu_alpha['low'], mu_n['low'])
        rules.append({
            'rule': 'Понизить заявку сильно',
            'value': round(min(mu_alpha['low'], mu_n['low']), 2),
            'is_max': 0
        })
        value = min(mu_alpha['low'], mu_n['high'])
        if max < value:
            max = value
            max_id = 1
        rules.append({
            'rule': 'Ничего не делать',
            'value': round(min(mu_alpha['low'], mu_n['high']), 2),
            'is_max': 0
        })
        value = min(mu_alpha['near1'], mu_n['low'])
        if max < value:
            max = value
            max_id = 2
        rules.append({
            'rule': 'Понизить заявку',
            'value': round(min(mu_alpha['near1'], mu_n['low']), 2),
            'is_max': 0
        })
        value = min(mu_alpha['near1'], mu_n['high'])
        if max < value:
            max = value
            max_id = 3
        rules.append({
            'rule': 'Повысить заявку',
            'value': round(min(mu_alpha['near1'], mu_n['high']), 2),
            'is_max': 0
        })
        value = min(mu_alpha['high'], mu_n['low'])
        if max < value:
            max = value
            max_id = 4
        rules.append({
            'rule': 'Ничего не делать',
            'value': round(min(mu_alpha['high'], mu_n['low']), 2),
            'is_max': 0
        })
        value = min(mu_alpha['high'], mu_n['high'])
        if max < value:
            max_id = 5
        rules.append({
            'rule': 'Повысить заявку сильно',
            'value': round(min(mu_alpha['high'], mu_n['high']), 2),
            'is_max': 0
        })
        rules[max_id]['is_max'] = 1
        return rules

    @staticmethod
    def get_tip_values(player):
        rules = FuzzyPromter.get_tip(player)
        for rule in rules:
            rule['rule_val'] = rule['value']
            if ("Повысить" in rule['rule']):
                rule['value'] = round(int(player.in_round(player.round_number - 1).units) * (1.0 + rule['value']))
            elif("Понизить" in rule['rule']):
                rule['value'] = round(int(player.in_round(player.round_number - 1).units) * (1.0 - rule['value']))
            else:
                rule['value'] = int(player.in_round(player.round_number - 1).units)
        print(rules)
        return rules



class KorginPromter():
    @staticmethod
    def calculate_korgin_value(group, player):
        players = group.get_players()
        sum = 0
        for _player in players:
            sum += _player.get_real_target_payoff() / _player.in_round(_player.round_number - 1).units
        C = sum - player.get_real_target_payoff() / player.in_round(player.round_number - 1).units
        return round((group.get_R() - player.get_real_target_payoff()) / C)


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


class Pair():
    key = None
    value = None

    def set_key_value(self, key, value):
        self.key = key
        self.value = value
