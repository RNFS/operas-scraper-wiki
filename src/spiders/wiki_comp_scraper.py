import  scrapy
import time 
import re

class ComposersScraper(scrapy.Spider):
    name = "wikicomp"

    def start_requests(self):
        urls = [
            "https://en.wikipedia.org/wiki/Category:Opera_composers_by_nationality",
            ] 

        for url in urls:
            yield scrapy.Request(url=url, callback=self.nat_parser)
    
    # get all nationalities links
    def nat_parser(self, response):
        nationalities =  response.xpath("//div[@id='mw-subcategories']//span[@class='CategoryTreeEmptyBullet']/following-sibling::a//@href").getall()
        domain = "https://en.wikipedia.org/"
        for nat in nationalities:
            if country := re.search(r"^.*:([a-zA-Z]*)_.*$", nat):
                country = country.group(1)
            else :
                country = "None"

            nat_url = domain + nat 
            print(country)
            yield scrapy.Request(url=nat_url, callback=self.pages_parser, meta={"country":country})
            time.sleep(5)

    def pages_parser(self, response):
        counrty = response.meta.get("country")

        domain = "https://en.wikipedia.org/"
        pages_list = response.xpath("//div[@id='mw-pages']//div[@class='mw-category-group']//li/a//@href").getall()
        
        for page in pages_list:
            page_url = domain + page
            yield scrapy.Request(url=page_url, callback=self.content_parser, meta={"country":counrty})

        # next page (button)
        if next_page := response.xpath("//div[@id='mw-pages']//*[text()[contains(.,'next page')]]/@href").get():    
            next_page= domain + next_page
            yield scrapy.Request(url=next_page, callback=self.pages_parser, meta={"country":counrty}) 

        if sub_categories := response.xpath("//div[@id='mw-subcategories']//a/@href").getall():
            for category in sub_categories:
                category_link = domain + category
                print(category_link)
                print("#" * 30)
                yield scrapy.Request(url=category_link, callback=self.pages_parser, meta={"country":counrty})
                time.sleep(5)
                    

    def content_parser(self, response):
        name = response.xpath("//span[@class='mw-page-title-main']/text()").get()
        era = None 
        year = None
        country = response.meta.get("country")
        # extract era from birthday if birth is avai 
        if birthdate := response.xpath("//table[@class='infobox vcard plainlist']//*[text()[contains(., 'Born')]]//following-sibling::td/text()").getall():
            birthdate= "".join(birthdate)
            year = re.search(r"(\d{4})", birthdate)
            if year:
                year = year.group(1)
                era = f"{year[:2]}th" 

        else :
            if birthdate := response.xpath("//*[text()[contains(., 'Born')]]//following-sibling::td/text()").getall():
                birthdate= "".join(birthdate)
                year = re.search(r"(\d{4})", birthdate)
                if year:
                    year = year.group(1)
                    era = f"{year[:2]}th"
        if date_of_death :=  response.xpath("//*[text()[contains(., 'Died')]]//following-sibling::td/text()").get():
            date_of_death = "".join(date_of_death)
    
        biography = response.xpath("//div[@class='mw-parser-output']/p/text()").getall()
        biography = "".join(biography)

        yield {
            "name": name,
            "birthdate": birthdate,
            "era" : era, 
            "country":country, 
            "date death": date_of_death,
            "biography": biography,
            }