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


class ResultsWaitPage(WaitPage):
    body_text = "Waiting for the other participant to decide."

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
