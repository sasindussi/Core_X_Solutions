import traceback

try:
  from app import app as application

  app = application
except Exception as e:
  print("CRASHED DURING IMPORT:")
  traceback.print_exc()
  raise e
