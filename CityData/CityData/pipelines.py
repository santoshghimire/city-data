# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
from collections import  OrderedDict
import json
import codecs


class CitydataPipeline(object):

    def process_item(self, item, spider):
        self.file = codecs.open('../data/{}.json'.format(item['stats']['zip']), 'wb',
                                encoding='utf-8')

        values = OrderedDict([
            ('zip', item['stats']['zip']),
            ('cities', item['stats']['cities']),
            ('county',item['stats']['county']),
            ('demographics',item['stats']['demographics']),
            ('local_businesses',item['stats']['local_businesses']),
            ('population_25_years_and_above', item['stats']['population_25_years_and_above']),
            ('population_15_years_and_above', item['stats']['population_15_years_and_above']),
            ('real_etates', item['stats']['real_etates']),
            ('housing_units_in_structures', item['stats']['housing_units_in_structures']),
            ('house_values_of_owner_occupied', item['stats']['house_values_of_owner_occupied']),
            ('household_income_distribution', item['stats']['household_income_distribution']),
            ('bedrooms_in_houses_and_apartments', item['stats']['bedrooms_in_houses_and_apartments']),
            ('vehicles_in_houses_and_apartments', item['stats']['vehicles_in_houses_and_apartments']),
            ('mean_house_price', item['stats']['mean_house_price']),
            ('median_house_value', item['stats']['median_house_value']),
            ('entry_of_foreign_born_population', item['stats']['entry_of_foreign_born_population']),
            ('travel_time_to_work', item['stats']['travel_time_to_work']),
            ('races', item['stats']['races']),
            ('rent_paid_by_renters', item['stats']['rent_paid_by_renters']),
            ('first_ancestries', item['stats']['first_ancestries']),
            ('neighborhoods', item['stats']['neighborhoods']),
            ('foreign_born_residents', item['stats']['foreign_born_residents']),
            ('transportation', item['stats']['transportation']),
            ('facilities', item['stats']['facilities'])
        ])
        item = {
            'stats': values
        }

        line = json.dumps(item, sort_keys=False) + "\n"
        self.file.write(line)

        return item
