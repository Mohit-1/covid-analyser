import os
import json
import argparse
import requests
from tabulate import tabulate


class Covid_Analyser:
    def __init__(self):
        self.response_json = None
        self.data_per_state = {}
        self.raw_file_path = None

    def get_data(self):
        response = requests.get('https://api.covid19india.org/data.json')

        base_dir = os.path.dirname(os.path.abspath(__file__))
        raw_file_path = f'{base_dir}/covid_raw_data.json'
        self.response_json = json.loads(response.content)

        with open(raw_file_path, 'w') as f:
            f.write(json.dumps(self.response_json))

        self.raw_file_path = raw_file_path

    def get_data_from_file(self, raw_file_path):
        with open(raw_file_path) as f:
            self.response_json = json.loads(f.read())

    def get_data_per_state(self):
        states_data = self.response_json.get('statewise')
        data_per_state = {}

        keys_to_filter = [
            'active', 'confirmed', 'deaths', 'recovered', 'state'
        ]

        for data in states_data:
            if data.get('state').lower() == 'total':
                continue

            data_per_state[data.get('statecode')] = {
                k: data.get(k) for k in keys_to_filter
            }

        self.data_per_state = data_per_state

    def get_state_codes(self):
        return self.data_per_state.keys()

    def get_state_for_code(self, state_code):
        return self.data_per_state.get(state_code).get('state')

    def get_outcomes(self, outcome_type='recovered', reverse=False, limit=None):
        if outcome_type not in ('active', 'recovered', 'deaths'):
            return []

        outcomes = []
        for state_code, data in self.data_per_state.items():
            try:
                outcome_ratio = round(
                    int(data[outcome_type]) / int(data['confirmed']), 6
                )

            except ZeroDivisionError:
                outcome_ratio = 0.0

            outcomes.append(
                {
                    'state_code': state_code, 
                    'state': data['state'],
                    f'{outcome_type}_ratio': outcome_ratio
                }
            )

        top_outcomes = sorted(
            outcomes, key=lambda x: x[f'{outcome_type}_ratio'],
            reverse=reverse
        )

        return top_outcomes[:limit] if limit else top_outcomes

    def get_outcome_for_state(self, outcomes, state_code):
        for i in range(len(outcomes)):
            if outcomes[i].get('state_code') == state_code:
                return i, outcomes[i]

        raise IndexError

    def get_scores(self, recoveries, actives, deaths):
        score_per_state = {}
        state_codes = self.get_state_codes()
        for state_code in state_codes:
            i, recov_meta = self.get_outcome_for_state(recoveries, state_code)
            recov_score = round(1 - (i / len(recoveries)), 6)

            i, active_meta = self.get_outcome_for_state(actives, state_code)
            active_score = round(1 - (i / len(actives)), 6)

            i, death_meta = self.get_outcome_for_state(deaths, state_code)
            death_score = round(1 - (i / len(deaths)), 6)
            score_per_state[state_code] = {
                'state': self.get_state_for_code(state_code),
                'recov_score': recov_score,
                'active_score': active_score,
                'death_score': death_score,
                'total_score': round(sum([recov_score, active_score, death_score]), 6),
                'recov_ratio': recov_meta.get('recovered_ratio'),
                'active_ratio': active_meta.get('active_ratio'),
                'death_ratio': death_meta.get('deaths_ratio')
            }

        return sorted(
            score_per_state.values(),
            key=lambda x: x['total_score'],
            reverse=True
        )


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--local', action='store_true')
    args = parser.parse_args()

    analyser = Covid_Analyser()

    if args.local:
        analyser.get_data_from_file('/home/mohit/Desktop/covid_raw_data.json')
    else:
        analyser.get_data()

    analyser.get_data_per_state()

    recoveries = analyser.get_outcomes(outcome_type='recovered', reverse=True)
    actives = analyser.get_outcomes(outcome_type='active')
    deaths = analyser.get_outcomes(outcome_type='deaths')

    scores = analyser.get_scores(recoveries, actives, deaths)
    scores = filter(lambda x: x['state'].lower() != 'state unassigned', scores)

    tabulate_scores = [
        [d['state'], d['total_score'], d['recov_score'], d['active_score'],
        d['death_score'], d['recov_ratio'], d['active_ratio'], d['death_ratio']]
        for d in scores
    ]

    print(
        tabulate(
            tabulate_scores,
            headers=[
                'State', 'Total score', 'Recov score', 'Active score', 'Death score', 'Recov ratio',
                'Active ratio', 'Death ratio'
                ],
            tablefmt='pretty'
        ),
        '\n'
    )
