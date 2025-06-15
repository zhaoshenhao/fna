from django.core.management.base import BaseCommand, CommandError
from webui.agent.run import Pipeline
# Import any other necessary modules (e.g., requests, csv, datetime)

# 0 2 * * * /path/to/yourprojectenv/bin/python /path/to/yourproject/manage.py crawler >> /path/to/yourproject/logs/cron.log 2>&1

class Command(BaseCommand):
    help = 'Populates the NewsArticles with data from a source.'

    # You can add arguments if your command needs them
    # def add_arguments(self, parser):
    #     parser.add_argument('source_file', type=str, help='Path to the data source file')

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting data population...'))

        try:
            p = Pipeline(workers=5)
            p.run()
            self.stdout.write(self.style.SUCCESS('Data population finished successfully.'))
        except Exception as e:
            # It's good practice to catch specific exceptions
            raise CommandError(f'Error during data population: {e}')
