import  scrapy
import time 
import re
import xml.etree.ElementTree as ET

 
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
        nationalities = response.xpath("//div[@id='mw-subcategories']//span[@class='CategoryTreeBullet']/following-sibling::a//@href | //div[@id='mw-subcategories']//span[@class='CategoryTreeEmptyBullet']/following-sibling::a//@href").getall()
        # nationalities =  response.xpath("//div[@id='mw-subcategories']//span[@class='CategoryTreeEmptyBullet']/following-sibling::a//@href").getall()
        domain = "https://en.wikipedia.org/"
        for nat in nationalities:
            if country := re.search(r"^.*:([a-zA-Z]*)_.*$", nat):
                country = country.group(1)
            else :
                country = "None"

            nat_url = domain + nat 

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
                yield scrapy.Request(url=category_link, callback=self.pages_parser, meta={"country":counrty})
                time.sleep(5)
                    

    def content_parser(self, response):
        name = response.xpath("//span[@class='mw-page-title-main']/text()").get()
        era = None 
        year = None
        birthdate = None
        style = None 
        date_of_death = None
        biography  = None  

        country = response.meta.get("country")
        if country == "New" :
            country = "New Zealand"
        elif country == "Opera":
            country = None            

        # extract era from birthday if birth is avai in different ways 
        birthdate_f= response.xpath("//*[text()[contains(., 'Born')]]//following-sibling::td/text()").getall()
        birthdate_s =response.xpath("//table[@class='infobox biography vcard']//*[text()[contains(., 'Born')]]//following-sibling::td/text()").getall()
        birthdate_t = response.xpath("//table[@class='infobox vcard plainlist']//*[text()[contains(., 'Born')]]//following-sibling::td/text()").getall()            
            
        if birthdate_f or birthdate_s or birthdate_t:  
            if birthdate := list(self.value_checker([birthdate_f, birthdate_s, birthdate_t])):
                birthdate= "".join(str(x) for x  in birthdate)
                birthdate ="".join(birthdate)
                birthdate = birthdate.replace("[", "")
                birthdate = birthdate.replace("]", "")
                birthdate = birthdate.replace(",", "")
                birthdate = birthdate.replace("'", "")
                

                year = re.search(r"(\d{4})", birthdate)
                if year:
                    year = year.group(1)
                    era = f"{year[:2]}th" 

        date_of_death_f = response.xpath("//table[@class='infobox biography vcard']//*[text()[contains(., 'Died')]]//following-sibling::td/text()").getall()
        date_of_death_s = response.xpath("//table[@class='infobox vcard plainlist']//*[text()[contains(., 'Died')]]//following-sibling::td/text()").getall() 
        date_of_death_t =  response.xpath("//*[text()[contains(., 'Died')]]//following-sibling::td/text()").get()
        if date_of_death_f or date_of_death_s or date_of_death_t:
            date_of_death = list(self.value_checker([date_of_death_f, date_of_death_s, date_of_death_t])) 
            
            date_of_death = "".join(str(x) for x  in  date_of_death)
            date_of_death = date_of_death.replace("[", "")
            date_of_death = date_of_death.replace("]", "")
            date_of_death = date_of_death.replace(",", "")
            date_of_death = date_of_death.replace("'", "")
            

        style_a = response.xpath("//table[@class='infobox biography vcard']//*[text()[contains(., 'Style')]]//following-sibling::td/text()").getall()
        style_b = response.xpath("//table[@class='infobox vcard plainlist']//*[text()[contains(., 'Style')]]//following-sibling::td/text()").getall() 
        style_c =  response.xpath("//*[text()[contains(., 'Style')]]//following-sibling::td/text()").getall()

        style_d = response.xpath("//table[@class='infobox biography vcard']//*[text()[contains(., 'Genres')]]//following-sibling::td/text()").getall()
        style_e = response.xpath("//table[@class='infobox vcard plainlist']//*[text()[contains(., 'Genres')]]//following-sibling::td/text()").getall() 
        style_f =  response.xpath("//*[text()[contains(., 'Genres')]]//following-sibling::td/text()").getall()
        
        if style_a or style_b or style_c or style_d or  style_e or style_f :
            style = list(*self.value_checker([style_a , style_b , style_c, style_d, style_e, style_f])) 
            style = "".join("".join(str(x) for x in style))
            style = "".join(style)
            style = style.replace(",", "")
            if not style:
                style = None


        if biography := response.xpath("//div[@class='mw-parser-output']/p/text()").getall():
            biography = "".join(biography)
        
        # writing as xml file 
        comp_ = ET.Element('composer')
        e_name = ET.SubElement(comp_, "name")
        e_era = ET.SubElement(comp_, "era")
        e_style = ET.SubElement(comp_, "style")
        e_birthdate = ET.SubElement(comp_, "birthdate")
        e_country = ET.SubElement(comp_, "nationality")
        e_date_of_death = ET.SubElement(comp_,"death")
        e_biography = ET.SubElement(comp_,"biography")

        e_name.text = name
        e_birthdate.text = birthdate
        e_era.text = era
        e_country.text = country
        e_style.text = style
        e_date_of_death.text = date_of_death
        e_biography.text = biography  
        
        b_xml = ET.tostring(comp_)
        with open("composers.xml", "ab") as f:
            f.write(b_xml)


        # yield {
        #     "name": name,
        #     "birthdate": birthdate,
        #     "era" : era, 
        #     "country":country, 
        #     "date death": date_of_death,
        #     "biography": biography,
        #     }

    def value_checker(self, args):
        for x in args:
            if x :
                yield x 
                break
            