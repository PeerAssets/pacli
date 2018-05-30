import csv
from pypeerassets.pautils import exponent_to_amount


def export_to_csv(cards, filename):
    '''export <cards> to csv <file>'''

    def format_card(card):
        '''filter out some info from CardTransfer'''

        c = card.__dict__.copy()
        c.pop("asset_specific_data")
        c["receiver"] = c["receiver"][0]
        c["amount"] = exponent_to_amount(c["amount"][0], card.number_of_decimals)
        c.pop("number_of_decimals")
        return c

    with open(filename, 'w') as csv_file:
        writer = csv.writer(csv_file, delimiter=';')
        writer.writerow(format_card(cards[0]).keys())  # writing the header
        for i in cards:
            writer.writerow(format_card(i).values())
