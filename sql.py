from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


class Component(Base):
    __tablename__ = 'component'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    time = Column(Float)
    output = Column(Integer)

    def __repr__(self):
        return self.name


def first_try():
    engine = create_engine('sqlite:///factorio.db', echo=True)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    # component = Component(name='Green circuit', time=0.5, output=1)
    # session.add(component)
    # session.commit()
    for instance in session.query(Component).order_by(Component.name):
        print(instance.name)


if __name__ == '__main__':
    first_try()
