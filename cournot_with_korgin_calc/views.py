from otree.common import safe_json

from . import models
from ._builtin import Page, WaitPage
from otree.api import Currency as c, currency_range
from .models import Constants


class Introduction(Page):
    def is_displayed(self):
        return self.round_number == 1


class Decide(Page):
    form_model = models.Player
    form_fields = ['units']

    def vars_for_template(self):
        # Filling the data for HighCharts graph
        if self.round_number != 1:
            requests = self.group.get_requests()
            payoffs = self.group.get_payoffs()
            id_in_group = self.player.id_in_group
            length = len(self.group.get_players())
            i = 0
            target_payoffs = []
            while i < length:
                if i+1 != id_in_group:
                    target_payoffs.append(None)
                else:
                    target_payoffs.append(self.player.get_target_payoff())
                i += 1

            series = [
                {
                    'name': 'Запрошено',
                    'data': requests
                },
                {
                    'name': 'Выдано',
                    'data': payoffs
                },
                {
                    'name': 'Оптимум',
                    'data': target_payoffs
                }
            ]

            highcharts_series = safe_json(series)

            return {
                'highcharts_series': highcharts_series
            }
        else:
            return {}


class ResultsWaitPage(WaitPage):
    body_text = "Ожидание других игроков."

    def after_all_players_arrive(self):
        self.group.set_payoffs()


class Results(Page):
    def vars_for_template(self):
        return {'total_plus_base': self.player.payoff}


page_sequence = [
    Introduction,
    Decide,
    ResultsWaitPage,
    Results
]
