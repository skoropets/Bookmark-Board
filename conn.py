from sqlalchemy import *
from sqlalchemy.orm import sessionmaker

engine = create_engine('mysql+mysqldb://root:samsung@localhost/board?use_unicode=1', echo=True)
session = sessionmaker(bind=engine)()
