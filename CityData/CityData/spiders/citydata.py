# -*- coding: utf-8 -*-
import scrapy
from scrapy.shell import inspect_response
from CityData.items import CitydataItem
import re


class CitydataSpider(scrapy.Spider):
    name = "citydata"
    allowed_domains = ["city-data.com"]
    start_urls = (
        # 'http://www.city-data.com/zipDir.html',
        'http://www.city-data.com/zips/19707.html',
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

        races_elem = main_body_elem.xpath(".//div[@class='row']/div[@class='col-md-8']/ul[@class='list-group']/li")[-1]
        races_dict = dict(
            zip(races_elem.xpath(".//li/text()").extract(), races_elem.xpath(".//li/span/text()").extract()))

        neighborhoods_name_list = main_body_elem.xpath("//div[@align='left']/ul/li/a/text()").extract()
        neighborhoods_link_list = main_body_elem.xpath("//div[@align='left']/ul/li/a/@href").extract()
        neighborhoods_link_list = [response.urljoin(link) for link in neighborhoods_link_list]

        neighborhoots_dict = dict(zip(neighborhoods_name_list, neighborhoods_link_list))

        real_states_href = response.xpath(
            '//a[contains(text(),"Recent home sales, real estate maps, and home value estimator for zip code")]/@href').extract_first()

        request = scrapy.Request(response.urljoin(real_states_href), self.parse_real_states)

        zip_code_dict = {
            "zip": code_group.group(1),
            "cities": county_cities[:-1],
            "county": county_cities[-1],
            "stats": {
                "population": {
                    "2013": 0,
                    "2010": 0,
                },
                "houses_and_condos": 0
            },
            'races': races_dict,
            'neighborhoods': neighborhoots_dict,
        }

        item = CitydataItem()
        item['ZipCode'] = zip_code_dict
        request.meta['main_url'] = response.url

        request.meta['item'] = item

        return request

    def parse_real_states(self, response):
        city_name = response.xpath("//h1/span/text()").extract_first()
        city_name = re.sub(r'\(.*', '', city_name)
        recent_home_sales_list = response.xpath("//ul[@class='listrecent']/li/text()").extract()

        sales_address_list = [x.split(":")[0] for x in recent_home_sales_list]
        sales_prices_list = [re.search(r'(\$\d+,+\d+)', x).group() for x in recent_home_sales_list]
        sales_date_list = [re.search(r'(\d\d\d\d-\d\d-\d\d)', x).group() for x in recent_home_sales_list]
        sales_home_type_list = [re.search(r'\(([^)]*)\)', x).group(1) for x in recent_home_sales_list]

        real_states_dict_list = []
        for x in range(len(sales_address_list)):
            real_states_dict = {}
            real_states_dict['address'] = sales_address_list[x]
            real_states_dict['price'] = sales_prices_list[x]
            real_states_dict['date'] = sales_date_list[x]
            real_states_dict['home_type'] = sales_home_type_list[x]
            real_states_dict_list.append(real_states_dict)
        item = response.meta['item']

        item['ZipCode']['real_etates'] = {
            'city': city_name,
            'home_sales': real_states_dict_list
        }

        # url = 'http://www.city-data.com/zips/19707.html'
        url = response.meta['main_url']
        request = scrapy.Request(url,self.parse_zip_code_again)

        request.meta['item'] = item
        return request

    def parse_zip_code_again(self,response):
        item = response.meta['item']

        main_body_elem = response.xpath("//div[@id='body']")[1]

        house_price_elem = main_body_elem.xpath("blockquote[3]/text()").extract()
        house_price = [x for x in house_price_elem if x.strip()]

        house_type_elem = main_body_elem.xpath("blockquote[3]/b/text()").extract()
        house_type = [x for x in house_type_elem if x.strip()]
        mean_house_prices_dict = dict(zip(house_type,house_price))

        item['ZipCode']['mean_house_price'] = mean_house_prices_dict

        """ Zip code 19707 household income distribution in 2013"""
        household_income_distribution_list = main_body_elem.xpath(".//ul[@class='list-group col-md-4 col-sm-6 col-xs-12'][1]/li/text()").extract()
        household_income_distribution_list=[x for x in household_income_distribution_list if x.strip()]

        household_income_distribution_count_list = main_body_elem.xpath(".//ul[@class='list-group col-md-4 col-sm-6 col-xs-12'][1]/li/span/text()").extract()
        household_income_distribution_count_list=[x for x in household_income_distribution_count_list if x.strip()]
        item['ZipCode']['household_income_distribution'] = dict(zip(household_income_distribution_list,household_income_distribution_count_list))


        """ Estimate of home value of owner-occupied houses/condos in 2013 in zip code 19707"""
        house_values_distribution_list = main_body_elem.xpath(".//ul[@class='list-group col-md-4 col-sm-6 col-xs-12'][2]/li/text()").extract()
        house_values_distribution_list = [x for x in house_values_distribution_list if x.strip()]
        house_values_distribution_count_list = main_body_elem.xpath(".//ul[@class='list-group col-md-4 col-sm-6 col-xs-12'][2]/li/span/text()").extract()
        house_values_distribution_count_list = [x for x in house_values_distribution_count_list if x.strip()]
        item['ZipCode']['house_values_of_owner_occupied'] = dict(zip(house_values_distribution_list, house_values_distribution_count_list))


        """ Rent paid by renters in 2013 in zip code 19707"""
        rent_paid_distribution_list = main_body_elem.xpath(
            ".//ul[@class='list-group col-md-4 col-sm-6 col-xs-12'][3]/li/text()").extract()
        rent_paid_distribution_list = [x for x in rent_paid_distribution_list if x.strip()]
        rent_paid_distribution_count_list = main_body_elem.xpath(
            ".//ul[@class='list-group col-md-4 col-sm-6 col-xs-12'][3]/li/span/text()").extract()
        rent_paid_distribution_count_list = [x for x in rent_paid_distribution_count_list if x.strip()]
        item['ZipCode']['rent_paid_by_renters'] = dict(
            zip(rent_paid_distribution_list, rent_paid_distribution_count_list))

        """Means of transportation to work in zip code 19707"""
        transportation_type_list = main_body_elem.xpath(".//ul[@class='list-group col-md-4 col-sm-6 col-xs-12'][4]/li/text()").extract()
        transportation_type_number_list = main_body_elem.xpath(".//ul"
                                                               "[@class='list-group col-md-4 col-sm-6 col-xs-12'][4]/"
                                                               "li/span[@class='badge']/text()").extract()

        transportation_dict = dict(zip(transportation_type_list,transportation_type_number_list))
        item['ZipCode']['transportation'] = transportation_dict


        """Travel time to work (commute) in zip code 19707"""

        travel_time_to_work_list= main_body_elem.xpath(".//ul[@class='list-group col-md-4 col-sm-6 col-xs-12'][5]/"
                                                       "li/text()").extract()
        transportation_type_work_count_list = main_body_elem.xpath(".//ul"
                                                               "[@class='list-group col-md-4 col-sm-6 col-xs-12'][5]/"
                                                               "li/span[@class='badge']/text()").extract()

        travel_time_to_work_dict = dict(zip(transportation_type_work_count_list,travel_time_to_work_list))
        item['ZipCode']['travel_time_to_work'] = travel_time_to_work_dict

        """ Most common Place of birth for the foreign born residents"""
        foreign_born_elem = main_body_elem.xpath(".//div[@class='col-md-6']/div[@class='gBorder']/ul")[0]
        country_list = foreign_born_elem.xpath("li/b/text()").extract()
        country_list = [country for country in country_list if country.strip()]

        country_percent_list = foreign_born_elem.xpath("li/span/text()").extract()
        country_percent_list = [percent for percent in country_percent_list if percent.strip()]

        item['ZipCode']['foreign_born_residents'] = dict(zip(country_list, country_percent_list))


        """ Most Common First Ancestries reported in 19707"""

        first_ancestries_elem = main_body_elem.xpath(".//div[@class='col-md-6']/div[@class='gBorder']/ul")[1]
        ancestor_list = first_ancestries_elem.xpath("li/b/text()").extract()
        ancestor_list =[ancestor for ancestor in ancestor_list if ancestor.strip()]

        ancestor_percent_list = first_ancestries_elem.xpath("li/span/text()").extract()
        ancestor_percent_list = [ancestor for ancestor in ancestor_percent_list if ancestor.strip()]

        item['ZipCode']['first_ancestries'] = dict(zip(ancestor_percent_list,ancestor_list))


        """ Year of entry of the foreign-born population"""

        year_of_entry_of_foreign_populaton_elem = main_body_elem.xpath(".//div[@class='col-md-6']/div[@class='gBorder']/ul")[2]
        entry_year_list = year_of_entry_of_foreign_populaton_elem.xpath("li/b/text()").extract()
        entry_year_list =[year for year in entry_year_list if year.strip()]

        year_popn_list = year_of_entry_of_foreign_populaton_elem.xpath("li/span/text()").extract()
        year_popn_list = [popn for popn in year_popn_list if popn.strip()]

        item['ZipCode']['entry_of_foreign_born_population'] = dict(zip(entry_year_list,year_popn_list))


        """Major facilities with environmental interests located in this zip code:"""

        facilities_elem = main_body_elem.xpath(".//ul[@style='margin-top: 0; margin-bottom: 0'][6]")

        school_list = []
        other_facilities_list= []

        for facility in facilities_elem.xpath("li"):
            facility = facility.xpath("text()").extract_first()

            if "school" in facility.lower():
                print("True")
                print(facility)
                school_list.append(facility)
            else:
                other_facilities_list.append(facility)
        facilities_dict = {
        'schools' : school_list,
        'other_facilities':other_facilities_list
        }

        item['ZipCode']['facilities'] =facilities_dict


        """" Housing Units in Structures """
        structure_type_list = main_body_elem.xpath(".//ul[@style='margin-top: 0; margin-bottom: 0'][4]/li/b/text()").extract()
        structure_type_list= [x for x in structure_type_list if x.strip()]

        structure_type_unit_list = main_body_elem.xpath(".//ul[@style='margin-top: 0; margin-bottom: 0'][4]/li/text()").extract()
        structure_type_unit_list=[x for x in structure_type_unit_list if x.strip()]

        item['ZipCode']['housing_units_in_structures'] =dict(zip(structure_type_list,structure_type_unit_list))


        """Estimated median house (or condo) value in 2013 for"""
        house_holder_type_list = main_body_elem.xpath(".//ul[@style='margin-top: 0; margin-bottom: 0'][3]/li/b/text()").extract()
        house_holder_type_list=[x for x in house_holder_type_list if x.strip()]

        median_value_list = main_body_elem.xpath(".//ul[@style='margin-top: 0; margin-bottom: 0'][3]/li/text()").extract()
        median_value_list=[x for x in median_value_list if x.strip()]

        item['ZipCode']['median_house_value'] =dict(zip(house_holder_type_list,median_value_list))

        """For population 25 years and over in 19707"""
        popn_25_years_and_above_type =main_body_elem.xpath(".//ul[@style='margin-top: 0; margin-bottom: 0'][1]/li/b/text()").extract()
        popn_25_years_and_above_type=[x for x in popn_25_years_and_above_type if x.strip()]

        popn_25_years_and_above_type_percent =main_body_elem.xpath(".//ul[@style='margin-top: 0; margin-bottom: 0'][1]/li/text()").extract()
        popn_25_years_and_above_type_percent=[x for x in popn_25_years_and_above_type_percent if x.strip()]

        item['ZipCode']['population_25_years_and_above'] =dict(zip(popn_25_years_and_above_type,popn_25_years_and_above_type_percent))

        """For population 15 years and over in 19707"""
        popn_15_years_and_above_type =main_body_elem.xpath(".//ul[@style='margin-top: 0; margin-bottom: 0'][2]/li/b/text()").extract()
        popn_15_years_and_above_type=[x for x in popn_15_years_and_above_type if x.strip()]

        popn_15_years_and_above_type_percent =main_body_elem.xpath(".//ul[@style='margin-top: 0; margin-bottom: 0'][2]/li/text()").extract()
        popn_15_years_and_above_type_percent=[x for x in popn_15_years_and_above_type_percent if x.strip()]

        item['ZipCode']['population_15_years_and_above'] =dict(zip(popn_15_years_and_above_type,popn_15_years_and_above_type_percent))

        """ Bedrooms in house and  Appartments """
        bedrooms_elem = main_body_elem.xpath(".//div[@class='hssData']")[0]
        """ Bedrooms in renter-occupied apartments in Hockessin, DE (19707)"""

        bedrooms_in_owner_house_elem = bedrooms_elem.xpath(".//ul")[0]

        bedrooms_type_in_owner_house_list = bedrooms_in_owner_house_elem.xpath("li/b/text()").extract()
        bedrooms_type_in_owner_house_list=[x for x in bedrooms_type_in_owner_house_list if x.strip()]

        bedrooms_type_count_in_owner_house_list = bedrooms_in_owner_house_elem.xpath("li/span/text()").extract()
        # bedrooms_type_count_in_owner_house_list=[x for x in bedrooms_type_count_in_owner_house_list if x.strip()]

        bedrooms_in_ownner_house_dict = dict(zip(bedrooms_type_in_owner_house_list,bedrooms_type_count_in_owner_house_list))


        """Bedrooms in owner-occupied houses and condos in Hockessin, DE (19707)"""
        bedrooms_in_renter_house_elem = bedrooms_elem.xpath(".//ul")[1]

        bedrooms_type_in_renter_house_list = bedrooms_in_renter_house_elem.xpath("li/b/text()").extract()
        bedrooms_type_in_renter_house_list = [x for x in bedrooms_type_in_renter_house_list if x.strip()]

        bedrooms_type_count_in_renter_house_list = bedrooms_in_renter_house_elem.xpath("li/span/text()").extract()
        bedrooms_type_count_in_renter_house_list = [x for x in bedrooms_type_count_in_renter_house_list if x.strip()]

        bedrooms_in_renter_house_dict = dict(zip(bedrooms_type_in_renter_house_list, bedrooms_type_count_in_renter_house_list))

        item['ZipCode']['bedrooms_in_houses_and_apartments'] ={
            'owner_occupied_houses' : bedrooms_in_ownner_house_dict,
            'renter_occupied_apartments' : bedrooms_in_renter_house_dict,
        }


        """ Cars and Vehicles  """
        vehicles_elem = main_body_elem.xpath(".//div[@class='hssData']")[1]
        """ Vehicles in renter-occupied apartments in Hockessin, DE (19707)"""

        vehicles_in_owner_house_elem = vehicles_elem.xpath(".//ul")[0]

        vehicles_type_in_owner_house_list = vehicles_in_owner_house_elem.xpath("li/b/text()").extract()
        vehicles_type_in_owner_house_list=[x for x in vehicles_type_in_owner_house_list if x.strip()]

        vehicles_type_count_in_owner_house_list = vehicles_in_owner_house_elem.xpath("li/span/text()").extract()
        vehicles_type_count_in_owner_house_list=[x for x in vehicles_type_count_in_owner_house_list if x.strip()]

        vehicles_in_ownner_house_dict = dict(zip(vehicles_type_in_owner_house_list,vehicles_type_count_in_owner_house_list))


        """Vehicles in owner-occupied houses and condos in Hockessin, DE (19707)"""
        vehicles_in_renter_house_elem = bedrooms_elem.xpath(".//ul")[1]

        vehicles_type_in_renter_house_list = vehicles_in_renter_house_elem.xpath("li/b/text()").extract()
        vehicles_type_in_renter_house_list = [x for x in vehicles_type_in_renter_house_list if x.strip()]

        vehicles_type_count_in_renter_house_list = vehicles_in_renter_house_elem.xpath("li/span/text()").extract()
        vehicles_type_count_in_renter_house_list = [x for x in vehicles_type_count_in_renter_house_list if x.strip()]

        vehicles_in_renter_house_dict = dict(zip(vehicles_type_in_renter_house_list, vehicles_type_count_in_renter_house_list))

        item['ZipCode']['vehicles_in_houses_and_apartments'] ={
            'owner_occupied_houses' : vehicles_in_ownner_house_dict,
            'renter_occupied_apartments' : vehicles_in_renter_house_dict,
        }


        zip_code_map = response.xpath("//a[contains(text(),' Zip Code Map')]/@href").extract_first()

        # request = scrapy.Request(response.urljoin(zip_code_map),self.parse_zip_code_map)

        # request.meta['item'] = item



        return item
        # return  request
        # inspect_response(response,self)



    def parse_zip_code_map(self,response):
        item = response.meta['item']

        zip = item['ZipCode']['zip']

        zip_code_map_elem = response.xpath("//div[@id='{}']".format(zip))


        inspect_response(response,self)
