import scrapy 
import time
import re
import xml.etree.ElementTree as ET


class OperasScraper(scrapy.Spider):
    name = "wiki_operas"

    # loop over the years by adding 10 years every time and wiki will get us all the years avai in this decade
    def start_requests(self):
        decade = 1590
        while decade <= 2023:
            urls = [
                f"https://en.wikipedia.org/wiki/Category:{decade}s_operas",
                ] 
            for url in urls:
                yield scrapy.Request(url=url, callback=self.de_parser)
                time.sleep(5)
                print(decade)
            decade += 10
    
    # decades parser
    def de_parser(self, response):
        list_years = response.xpath("//div[@class='mw-category-group']//a/@href").getall()
        domain = "https://en.wikipedia.org/"
        for next_year in list_years:
            if year := re.search(r"^.*:(\d{4}).*$",next_year):
                print(year)
                year = year.group(1)
            else:
                year = None                
            next_year = domain + next_year
            # decade = response.meta.get("decade")
            yield scrapy.Request(next_year, callback=self.year_parser,meta={"year":year})

    # years parser
    def year_parser(self, response):
        operas = response.xpath("//div[@class='mw-category-group']//@href").getall()
        year = response.meta.get("year")
        for opera in operas:
            opera_link = response.urljoin(opera)
            yield scrapy.Request(opera_link, callback=self.opera_content_parser, meta={"year":year})

    # page-content-parser
    def opera_content_parser(self, response):
        name = response.xpath("//h1/i/text()").get()
        year = response.meta.get("year")
        era = "".join(year[:2])
        # made_by = response.xpath("//table[@class='infobox vevent']//a/text()").getall()
        made_by =  response.xpath("//td[@class='infobox-subheader']//text()").getall()
        le = len(made_by)
        composers = None
        if le > 2 :
             composers = ", ".join(made_by[2:le])

        # pr = response.xpath("//td[@class='infobox-data']/text()").getall()     
        date = response.xpath("//div[@class='vevent']/text()").get()
        place = response.xpath("//div[@class='summary']//text()").getall()
        place = "".join(place)   
        summray  =  response.xpath("//table[@class='infobox vevent']/following-sibling::p/text()").getall()   
        summary = "".join(summray)   
        librettist =response.xpath("//table[@class='infobox vevent']//*[text()[contains(.,'Librettist')]]/following-sibling::td//text()").get() 
        language =  response.xpath("//table[@class='infobox vevent']//*[text()[contains(.,'Language')]]/following-sibling::td/text()").get()


        ## writing as xml foramt
        opera_ = ET.Element('opera')
        e_name = ET.SubElement(opera_, "name")
        e_composers = ET.SubElement(opera_, "composers")
        e_date = ET.SubElement(opera_, "premieredate")
        e_place = ET.SubElement(opera_, "premiereplace")
        e_language= ET.SubElement(opera_,"language")
        e_era = ET.SubElement(opera_,"era")
        e_librettist =  ET.SubElement(opera_,"librettist")  
        e_year = ET.SubElement(opera_,"year")
        e_summary = ET.SubElement(opera_,"summary")

        e_name.text = name
        e_composers.text = composers
        e_era.text = era
        e_place.text = place
        e_date.text = date
        e_language.text =  language
        e_librettist.text = librettist  
        e_year.text = year
        e_summary.text = summary

        b__xml = ET.tostring(opera_)
        with open("operas.xml", "ab") as f:
            f.write(b__xml)


        # yield {
            
        #     "name": name,
        #     "composers": composers,
        #     "premiere_date": date,
        #     "premiere_place": place,
        #     "Language" : language,
        #     "era" : f"{era}th",
        #     "librettist": librettist,
        #     "year": year, 
        #     "summary": summary 
        # }

