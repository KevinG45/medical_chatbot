# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter


class ValidationPipeline:
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        
        # Validate required fields
        if not adapter.get('name'):
            raise DropItem(f"Missing name in {item}")
            
        return item


class CleaningPipeline:
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        
        # Clean text fields
        for field_name in ['name', 'speciality', 'city', 'experience', 'location', 'fees']:
            value = adapter.get(field_name)
            if value:
                adapter[field_name] = str(value).strip()
                
        return item


class CsvExportPipeline:
    def process_item(self, item, spider):
        # This pipeline is handled by FEEDS setting
        return item


class DatabasePipeline:
    def process_item(self, item, spider):
        # Database storage can be implemented here
        return item