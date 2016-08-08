# -*- coding: utf-8 -*-
import scrapy
from scrapy.shell import inspect_response
from CityData.items import CitydataItem
import re
from scrapy import Selector

class CitydataSpider(scrapy.Spider):
    name = "citydata"
    allowed_domains = ["city-data.com"]
    start_urls = (
        # 'http://www.city-data.com/zipDir.html',
        'http://www.city-data.com/zips/19707.html',
        'http://www.city-data.com/zips/98101.html',
    )

    # def parse(self, response):
    #
    #     print response.urljoin("sdfs")
    #
    #     zip_code_range_elem = response.xpath("//div[@class='list-group row']/a/@href").extract()
    #
    #     for zip_code_range in zip_code_range_elem:
    #         zip_code_range_link = response.urljoin(zip_code_range)
    #         yield scrapy.Request(zip_code_range_link, self.parse_zip_codes_list)
    #
    #
    #
    #     # inspect_response(response,self)
    #
    #
    #
    # def parse_zip_codes_list(self,response):
    #     # inspect_response(response,self)
    #     zip_codes_list_elem = response.xpath("//div[@class='list-group row']/a/@href").extract()
    #
    #     for zip_code_href in zip_codes_list_elem:
    #         code_group = re.search('\/zips\/(\d+)\.html', zip_code_href)
    #         if code_group.group(1).strip() == '19707':
    #
    #             zip_code_link = response.urljoin(zip_code_href)
    #
    #             yield scrapy.Request(zip_code_link,self.parse_zip_code)


    # def parse_zip_code(self, response):
    #
    #     inspect_response(response,self)


    def parse(self, response):
        # inspect_response(response,self)

        main_body_elem = response.xpath("//div[@id='body']")[1]
        # county_cities_elem = main_body_elem.xpath("normalize-space(.//div[@class='alert alert-success'])").extract_first()
        # county_cities = re.sub(r'\([^)]*\)','',county_cities_elem)
        county_cities = main_body_elem.xpath(".//div[@class='alert alert-success']/a/text()").extract()
        code_group = re.search('\/zips\/(\d+)\.html', response.url)
        zip_code = ""
        if code_group:
            try:
                zip_code = int(code_group.group(1))
            except:
                zip_code = code_group.group(1)

        print("***********************")
        # zip_code_map_elem = response.xpath("//div[@class='']").extract_first()
        sel = Selector(text=main_body_elem.extract())
        data = sel.xpath("string()").extract_first()
        data = data.split("\r\n")
        print(data)
        print("***********************")

        """ Profiles of Local Business"""
        local_business_elem = main_body_elem.xpath(".//div[@id='prbox']/table")
        local_business_name_list= local_business_elem.xpath(".//a/text()").extract()
        local_business_name_list= [x.strip() for x in local_business_name_list if x]

        local_business_link_list = local_business_elem.xpath(".//a/@href").extract()
        local_business_link_list= [response.urljoin(x.strip()) for x in local_business_link_list if x]
        local_business_dict_list = dict(zip(local_business_name_list,local_business_link_list))



        """ Races """
        races_elem = main_body_elem.xpath(".//div[@class='row']/div[@class='col-md-8']/ul[@class='list-group']/li")[-1]

        races_list = races_elem.xpath(".//li/text()").extract()
        races_count_list = races_elem.xpath(".//li/span/text()").extract()
        races_count_list = [int(x.replace(",", "")) for x in races_count_list if x]
        races_dict = dict(zip(races_list, races_count_list))

        """ Neighborhoods """

        neighborhoods_name_list = main_body_elem.xpath("//div[@align='left']/ul/li/a/text()").extract()
        neighborhoods_link_list = main_body_elem.xpath("//div[@align='left']/ul/li/a/@href").extract()
        neighborhoods_link_list = [response.urljoin(link) for link in neighborhoods_link_list]
        neighborhoods_dict = dict(zip(neighborhoods_name_list, neighborhoods_link_list))

        """ Real eestates"""

        real_estates_href = response.xpath(
            '//a[contains(text(),"Recent home sales, real estate maps, and home value estimator for zip code")]/@href').extract_first()

        request = scrapy.Request(response.urljoin(real_estates_href), self.parse_real_estates)


        item = CitydataItem()
        item['stats'] = {
            "zip": zip_code,
            "cities": county_cities[:-1],
            "county": county_cities[-1],
            'local_businesses' : local_business_dict_list,
            'races': races_dict,
            'neighborhoods': neighborhoods_dict,
        }

        request.meta['main_url'] = response.url
        request.meta['item'] = item

        return request

    def parse_real_estates(self, response):
        # inspect_response(response,self)

        city_name = response.xpath("//h1/span/text()").extract_first()
        city_name = re.sub(r'\(.*', '', city_name)
        recent_home_sales_list = response.xpath("//ul[@class='listrecent']/li/text()").extract()

        sales_address_list = [x.split(":")[0] for x in recent_home_sales_list]
        sales_prices_list = [re.search(r'(\$\d+,+\d+)', x).group() for x in recent_home_sales_list]
        sales_prices_list = [float(re.sub(r'[\$,]+', "",x.strip())) for x in sales_prices_list]

        sales_date_list = [re.search(r'(\d\d\d\d-\d\d-\d\d)', x).group() for x in recent_home_sales_list]
        sales_home_type_list = [re.search(r'\(([^)]*)\)', x).group(1) for x in recent_home_sales_list]

        real_estates_dict_list = []
        for x in range(len(sales_address_list)):
            real_estates_dict = {}
            real_estates_dict['address'] = sales_address_list[x]
            real_estates_dict['price'] = sales_prices_list[x]
            real_estates_dict['date'] = sales_date_list[x]
            real_estates_dict['home_type'] = sales_home_type_list[x]
            real_estates_dict_list.append(real_estates_dict)


        item = response.meta['item']
        item['stats']['real_etates'] = {
            'city': city_name,
            'home_sales': real_estates_dict_list
        }

        # url = 'http://www.city-data.com/zips/19707.html'
        url = response.meta['main_url']
        request = scrapy.Request(url, self.parse_zip_code_again)

        request.meta['item'] = item
        return request

    def parse_zip_code_again(self, response):
        item = response.meta['item']
        # inspect_response(response,self)

        main_body_elem = response.xpath("//div[@id='body']")[1]

        house_price_elem = main_body_elem.xpath("blockquote[3]/text()").extract()
        house_price = [float(re.sub(r'[\$,]+',"",x.strip())) for x in house_price_elem if x.strip()]
        house_type_elem = main_body_elem.xpath("blockquote[3]/b/text()").extract()
        house_type = [x.strip(":") for x in house_type_elem if x.strip()]
        mean_house_prices_dict = dict(zip(house_type, house_price))

        item['stats']['mean_house_price'] = mean_house_prices_dict

        """ Zip code 19707 household income distribution in 2013"""
        household_income_distribution_list = main_body_elem.xpath(
            ".//ul[@class='list-group col-md-4 col-sm-6 col-xs-12'][1]/li/text()").extract()
        household_income_distribution_list = [x for x in household_income_distribution_list if x.strip()]

        household_income_distribution_count_list = main_body_elem.xpath(
            ".//ul[@class='list-group col-md-4 col-sm-6 col-xs-12'][1]/li/span/text()").extract()
        household_income_distribution_count_list = [int(re.sub(r'[,]+','',x.strip()))
                                                    for x in household_income_distribution_count_list if x.strip()]

        item['stats']['household_income_distribution'] = dict(
            zip(household_income_distribution_list, household_income_distribution_count_list))

        """ Estimate of home value of owner-occupied houses/condos in 2013 in zip code 19707"""

        house_values_distribution_list = main_body_elem.xpath(
            ".//ul[@class='list-group col-md-4 col-sm-6 col-xs-12'][2]/li/text()").extract()

        house_values_distribution_list = [x for x in house_values_distribution_list if x.strip()]

        house_values_distribution_count_list = main_body_elem.xpath(
            ".//ul[@class='list-group col-md-4 col-sm-6 col-xs-12'][2]/li/span/text()").extract()

        house_values_distribution_count_list = [int(re.sub(r'[,]+','',x.strip()))
                                                for x in house_values_distribution_count_list if x.strip()]
        item['stats']['house_values_of_owner_occupied'] = dict(
            zip(house_values_distribution_list, house_values_distribution_count_list))

        """ Rent paid by renters in 2013 in zip code 19707"""

        rent_paid_distribution_list = main_body_elem.xpath(
            ".//ul[@class='list-group col-md-4 col-sm-6 col-xs-12'][3]/li/text()").extract()

        rent_paid_distribution_list = [x for x in rent_paid_distribution_list if x.strip()]

        rent_paid_distribution_count_list = main_body_elem.xpath(
            ".//ul[@class='list-group col-md-4 col-sm-6 col-xs-12'][3]/li/span/text()").extract()

        rent_paid_distribution_count_list = [int(re.sub(r'[,]+','',x.strip()))
                                              for x in rent_paid_distribution_count_list if x.strip()]
        item['stats']['rent_paid_by_renters'] = dict(
            zip(rent_paid_distribution_list, rent_paid_distribution_count_list))

        """Means of transportation to work in zip code 19707"""
        transportation_type_list = main_body_elem.xpath(
            ".//ul[@class='list-group col-md-4 col-sm-6 col-xs-12'][4]/li/text()").extract()

        transportation_type_count_list = main_body_elem.xpath(
            ".//ul[@class='list-group col-md-4 col-sm-6 col-xs-12'][4]/li/span[@class='badge']/text()").extract()

        transportation_type_count_list = [
            int(re.sub(r'[,]+', '', x.strip())) for x in transportation_type_count_list if x.strip()]

        transportation_dict = dict(zip(transportation_type_list, transportation_type_count_list))
        item['stats']['transportation'] = transportation_dict

        """Travel time to work (commute) in zip code 19707"""

        travel_time_to_work_list = main_body_elem.xpath(".//ul[@class='list-group col-md-4 col-sm-6 col-xs-12'][5]/"
                                                        "li/text()").extract()
        transportation_type_work_count_list = main_body_elem.xpath(
            ".//ul[@class='list-group col-md-4 col-sm-6 col-xs-12'][5]/li/span[@class='badge']/text()").extract()

        transportation_type_work_count_list = [
            int(re.sub(r'[,]+', '', x.strip())) for x in transportation_type_work_count_list if x.strip()]

        travel_time_to_work_dict = dict(zip(travel_time_to_work_list, transportation_type_work_count_list))
        item['stats']['travel_time_to_work'] = travel_time_to_work_dict

        """ Most common Place of birth for the foreign born residents"""
        foreign_born_elem = main_body_elem.xpath(".//div[@class='col-md-6']/div[@class='gBorder']/ul")[0]
        country_list = foreign_born_elem.xpath("li/b/text()").extract()
        country_list = [x.strip() for x in country_list if x.strip()]

        country_percent_list = foreign_born_elem.xpath("li/span/text()").extract()
        country_percent_list = [float(x.strip("%"))/100 if "%" in x else x for x in country_percent_list ]

        item['stats']['foreign_born_residents'] = dict(zip(country_list, country_percent_list))

        """ Most Common First Ancestries reported in 19707"""

        first_ancestries_elem = main_body_elem.xpath(".//div[@class='col-md-6']/div[@class='gBorder']/ul")[1]
        ancestor_list = first_ancestries_elem.xpath("li/b/text()").extract()
        ancestor_list = [x.strip() for x in ancestor_list if x.strip()]

        ancestor_percent_list = first_ancestries_elem.xpath("li/span/text()").extract()
        ancestor_percent_list = [float(x.strip("%"))/100 if "%" in x else x for x in ancestor_percent_list]

        item['stats']['first_ancestries'] = dict(zip(ancestor_list, ancestor_percent_list))

        """ Year of entry of the foreign-born population"""

        year_of_entry_of_foreign_populaton_elem = main_body_elem.xpath(
            ".//div[@class='col-md-6']/div[@class='gBorder']/ul")[2]

        entry_year_list = year_of_entry_of_foreign_populaton_elem.xpath("li/b/text()").extract()
        entry_year_list = [year for year in entry_year_list if year.strip()]

        year_popn_count_list = year_of_entry_of_foreign_populaton_elem.xpath("li/span/text()").extract()
        year_popn_count_list = [int(re.sub(r'[,]+', '', x.strip())) for x in year_popn_count_list if x.strip()]

        item['stats']['entry_of_foreign_born_population'] = dict(zip(entry_year_list, year_popn_count_list))

        """Major facilities with environmental interests located in this zip code:"""

        facilities_elem = main_body_elem.xpath(".//ul[@style='margin-top: 0; margin-bottom: 0'][6]")

        school_list = []
        other_facilities_list = []
        for facility in facilities_elem.xpath("li"):
            facility = facility.xpath("text()").extract_first()

            if "school" in facility.lower():
                print("True")
                print(facility)
                school_list.append(facility.strip())
            else:
                other_facilities_list.append(facility.strip())
        facilities_dict = {
            'schools': school_list,
            'other_facilities': other_facilities_list
        }

        item['stats']['facilities'] = facilities_dict

        """" Housing Units in Structures """
        structure_type_list = main_body_elem.xpath(
            ".//ul[@style='margin-top: 0; margin-bottom: 0'][4]/li/b/text()").extract()
        structure_type_list = [x.strip(":")  for x in structure_type_list if x.strip()]

        structure_type_unit_list = main_body_elem.xpath(
            ".//ul[@style='margin-top: 0; margin-bottom: 0'][4]/li/text()").extract()
        structure_type_unit_list = [int(re.sub(r'[,]+', '', x.strip())) for x in structure_type_unit_list if x.strip()]

        item['stats']['housing_units_in_structures'] = dict(zip(structure_type_list, structure_type_unit_list))

        """Estimated median house (or condo) value in 2013 for"""
        house_holder_type_list = main_body_elem.xpath(
            ".//ul[@style='margin-top: 0; margin-bottom: 0'][3]/li/b/text()").extract()
        house_holder_type_list = [x.strip(":") for x in house_holder_type_list if x.strip()]

        median_value_list = main_body_elem.xpath(
            ".//ul[@style='margin-top: 0; margin-bottom: 0'][3]/li/text()").extract()
        median_value_list = [float(re.sub(r'[\$,]+', '', x.strip())) for x in median_value_list if x.strip()]

        item['stats']['median_house_value'] = dict(zip(house_holder_type_list, median_value_list))

        """For population 25 years and over in 19707"""
        popn_25_years_and_above_type = main_body_elem.xpath(
            ".//ul[@style='margin-top: 0; margin-bottom: 0'][1]/li/b/text()").extract()
        popn_25_years_and_above_type = [x.strip(":") for x in popn_25_years_and_above_type if x.strip()]

        popn_25_years_and_above_type_percent = main_body_elem.xpath(
            ".//ul[@style='margin-top: 0; margin-bottom: 0'][1]/li/text()").extract()
        popn_25_years_and_above_type_percent = [
            float(x.strip("%"))/100 if "%" in x else x for x in popn_25_years_and_above_type_percent]

        item['stats']['population_25_years_and_above'] = dict(
            zip(popn_25_years_and_above_type, popn_25_years_and_above_type_percent))

        """For population 15 years and over in 19707"""
        popn_15_years_and_above_type = main_body_elem.xpath(
            ".//ul[@style='margin-top: 0; margin-bottom: 0'][2]/li/b/text()").extract()

        popn_15_years_and_above_type = [x.strip(":") for x in popn_15_years_and_above_type if x.strip()]

        popn_15_years_and_above_type_percent = main_body_elem.xpath(
            ".//ul[@style='margin-top: 0; margin-bottom: 0'][2]/li/text()").extract()

        popn_15_years_and_above_type_percent = [
            float(x.strip("%"))/100 if "%" in x else x for x in popn_15_years_and_above_type_percent ]

        item['stats']['population_15_years_and_above'] = dict(
            zip(popn_15_years_and_above_type, popn_15_years_and_above_type_percent))

        """ Bedrooms in house and  Appartments """
        bedrooms_elem = main_body_elem.xpath(".//div[@class='hssData']")[0]
        """ Bedrooms in renter-occupied apartments in Hockessin, DE (19707)"""

        bedrooms_in_owner_house_elem = bedrooms_elem.xpath(".//ul")[0]

        bedrooms_type_in_owner_house_list = bedrooms_in_owner_house_elem.xpath("li/b/text()").extract()
        bedrooms_type_in_owner_house_list = [x for x in bedrooms_type_in_owner_house_list if x.strip()]

        bedrooms_type_count_in_owner_house_list = bedrooms_in_owner_house_elem.xpath("li/span/text()").extract()
        bedrooms_type_count_in_owner_house_list = [
            int(re.sub(r'[,]+', '', x.strip())) for x in bedrooms_type_count_in_owner_house_list if x.strip()]

        bedrooms_in_ownner_house_dict = dict(
            zip(bedrooms_type_in_owner_house_list, bedrooms_type_count_in_owner_house_list))

        """Bedrooms in owner-occupied houses and condos in Hockessin, DE (19707)"""

        bedrooms_in_renter_house_elem = bedrooms_elem.xpath(".//ul")[1]

        bedrooms_type_in_renter_house_list = bedrooms_in_renter_house_elem.xpath("li/b/text()").extract()
        bedrooms_type_in_renter_house_list = [x for x in bedrooms_type_in_renter_house_list if x.strip()]

        bedrooms_type_count_in_renter_house_list = bedrooms_in_renter_house_elem.xpath("li/span/text()").extract()
        bedrooms_type_count_in_renter_house_list = [
            int(re.sub(r'[,]+', '', x.strip())) for x in bedrooms_type_count_in_renter_house_list if x.strip()]

        bedrooms_in_renter_house_dict = dict(
            zip(bedrooms_type_in_renter_house_list, bedrooms_type_count_in_renter_house_list))

        item['stats']['bedrooms_in_houses_and_apartments'] = {
            'owner_occupied_houses': bedrooms_in_ownner_house_dict,
            'renter_occupied_apartments': bedrooms_in_renter_house_dict,
        }

        """ Cars and Vehicles  """
        vehicles_elem = main_body_elem.xpath(".//div[@class='hssData']")[1]
        """ Vehicles in renter-occupied apartments in Hockessin, DE (19707)"""

        vehicles_in_owner_house_elem = vehicles_elem.xpath(".//ul")[0]

        vehicles_type_in_owner_house_list = vehicles_in_owner_house_elem.xpath("li/b/text()").extract()
        vehicles_type_in_owner_house_list = [x for x in vehicles_type_in_owner_house_list if x.strip()]

        vehicles_type_count_in_owner_house_list = vehicles_in_owner_house_elem.xpath("li/span/text()").extract()
        vehicles_type_count_in_owner_house_list = [
            int(re.sub(r'[,]+', '', x.strip())) for x in vehicles_type_count_in_owner_house_list if x.strip()]

        vehicles_in_ownner_house_dict = dict(
            zip(vehicles_type_in_owner_house_list, vehicles_type_count_in_owner_house_list))

        """Vehicles in owner-occupied houses and condos in Hockessin, DE (19707)"""
        vehicles_in_renter_house_elem = bedrooms_elem.xpath(".//ul")[1]

        vehicles_type_in_renter_house_list = vehicles_in_renter_house_elem.xpath("li/b/text()").extract()
        vehicles_type_in_renter_house_list = [x for x in vehicles_type_in_renter_house_list if x.strip()]

        vehicles_type_count_in_renter_house_list = vehicles_in_renter_house_elem.xpath("li/span/text()").extract()
        vehicles_type_count_in_renter_house_list = [
            int(re.sub(r'[,]+', '', x.strip())) for x in vehicles_type_count_in_renter_house_list if x.strip()]

        vehicles_in_renter_house_dict = dict(
            zip(vehicles_type_in_renter_house_list, vehicles_type_count_in_renter_house_list))

        item['stats']['vehicles_in_houses_and_apartments'] = {
            'owner_occupied_houses': vehicles_in_ownner_house_dict,
            'renter_occupied_apartments': vehicles_in_renter_house_dict,
        }

        zip_code_map = response.xpath("//a[contains(text(),' Zip Code Map')]/@href").extract_first()

        request = scrapy.Request(response.urljoin(zip_code_map), self.parse_zip_code_map)

        request.meta['item'] = item
        yield request
        # inspect_response(response,self)

    def parse_zip_code_map(self, response):

        item = response.meta['item']

        zip_code = item['stats']['zip']

        zip_code_map_elem = response.xpath("//div[@id='{}']".format(zip_code)).extract_first()
        sel = Selector(text=zip_code_map_elem)
        data = sel.xpath("string()").extract_first()
        data = data.split("\r\n")
        """population """
        population_data = [x.strip() for x in data if "zip code population in " in x.lower()]
        population_year_list = [
            re.search(r'\d\d\d\d', x.split(":")[0]).group() if ":" in x else x for x in population_data]

        population_count_list = [
            re.search(r'[\d,.]+', x.split(":")[1]).group() if ":" in x else x for x in population_data]

        population_count_list = [int(re.sub(r'[,]+', '', x.strip())) for x in population_count_list if x.strip()]

        population_data_dict = dict(zip(population_year_list,population_count_list))
        print(population_data_dict)

        """"   Area """
        area = [x.strip() for x in data if "area" in x.lower()]
        area_type = [x.split(":")[0].strip() if ":" in x else "" for x in area]
        area_measurement = [x.split(":")[1].strip() if ":" in x else "" for x in area]
        area_dict = dict(zip(area_type, area_measurement))
        print(area_dict)

        """ Population Density """

        population_density = [x.split(":")[1] for x in data if 'population density' in x.lower()]

        """ Median Real Estate property taxes"""

        with_mortgages = 'median real estate property taxes paid for housing units with mortgages'
        without_mortgage = 'median real estate property taxes paid for housing units with no mortgage'

        """ With Mortgages"""
        median_property_taxes_with_mortgages = [x.strip() for x in data if with_mortgages.lower() in x.lower()]

        taxes_with_mortgages_year = [re.search(r'\d\d\d\d', x.split(":")[0]).group() if ":" in x else x for x in
                                     median_property_taxes_with_mortgages]

        taxes_with_mortgages_amount = [re.search(r'\$[\d,.]+', x.split(":")[1]).group() if ":" in x else x for x in
                                       median_property_taxes_with_mortgages]

        taxes_with_mortgages_amount = [float(re.sub(r'[\$,]+', "", x.strip())) for x in taxes_with_mortgages_amount if x]

        taxes_with_mortgages_percent = [re.search(r'\(([^)]*)\)', x).group(1) if ":" in x else x for x in
                                        median_property_taxes_with_mortgages]
        taxes_with_mortgages_percent = [
            float(x.strip("%")) / 100 if "%" in x else x for x in taxes_with_mortgages_percent]

        taxes_with_mortgages_dict = []
        for x in range(len(taxes_with_mortgages_percent)):
            taxes_dict = {}
            taxes_dict['year'] = taxes_with_mortgages_year[x]
            taxes_dict['amount'] = taxes_with_mortgages_amount[x]
            taxes_dict['percent'] = taxes_with_mortgages_percent[x]
            taxes_with_mortgages_dict.append(taxes_dict)

        """ Without Mortgages"""

        median_property_taxes_without_mortgages = [x.strip() for x in data if without_mortgage.lower() in x.lower()]

        taxes_without_mortgages_year = [re.search(r'\d\d\d\d', x.split(":")[0]).group() if ":" in x else x for x in
                                        median_property_taxes_without_mortgages]

        taxes_without_mortgages_amount = [re.search(r'\$[\d,.]+', x.split(":")[1]).group() if ":" in x else x for x in
                                          median_property_taxes_without_mortgages]

        taxes_without_mortgages_amount = [
            float(re.sub(r'[\$,]+', "", x.strip())) for x in taxes_without_mortgages_amount if x]

        taxes_without_mortgages_percent = [re.search(r'\(([^)]*)\)', x).group(1) if ":" in x else x for x in
                                           median_property_taxes_without_mortgages]

        taxes_without_mortgages_percent = [
            float(x.strip("%")) / 100 if "%" in x else x for x in taxes_without_mortgages_percent]

        taxes_without_mortgages_dict = []
        for x in range(len(taxes_without_mortgages_percent)):
            taxes_dict = {}
            taxes_dict['year'] = taxes_without_mortgages_year[x]
            taxes_dict['amount'] = taxes_without_mortgages_amount[x]
            taxes_dict['percent'] = taxes_without_mortgages_percent[x]
            taxes_without_mortgages_dict.append(taxes_dict)

        median_real_estate_taxes = {
            'with mortgages': taxes_with_mortgages_dict,
            'with no mortgages': taxes_without_mortgages_dict
        }

        """ Remaining """
        median_monthly_owner_costs_for_units = [x.strip() for x in data if 'median monthly owner costs' in x.lower()]

        estimated_median_household_income = [x.strip() for x in data if 'estimated median' in x.lower()]
        median_gross_rent = [x.strip() for x in data if 'median gross rent' in x.lower()]
        print(median_gross_rent)
        unemployment = [x.strip() for x in data if 'unemployment' in x.lower()]
        print(unemployment)
        print ('******************')
        print(median_monthly_owner_costs_for_units)
        print(estimated_median_household_income)
        print(median_gross_rent)
        print(unemployment)
        print('******************')

        item['stats']['demographics'] = {
            'population': population_data_dict,
            'area': area_dict,
            'population_density': population_density[0],
            'median_real_estate_property_taxes_paid_for_housing': median_real_estate_taxes,

        }

        # inspect_response(response, self)

        yield item
