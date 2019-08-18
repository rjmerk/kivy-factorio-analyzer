from sqlalchemy import (
    create_engine, Column, Integer, String, Float, ForeignKey)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.orm.exc import NoResultFound

Base = declarative_base()


class Component(Base):
    __tablename__ = 'component'
    id = Column(Integer, primary_key=True)
    name = Column(String)

    def __repr__(self):
        return self.name


class Recipe(Base):
    __tablename__ = 'recipe'
    id = Column(Integer, primary_key=True)
    time = Column(Float)
    output_id = Column(Integer, ForeignKey('component.id'))
    output = relationship('Component')
    output_amount = Column(Float)


class RecipeInput(Base):
    __tablename__ = 'recipe_input'
    id = Column(Integer, primary_key=True)
    recipe_id = Column(Integer, ForeignKey('recipe.id'))
    recipe = relationship('Recipe')
    component_id = Column(Integer, ForeignKey('component.id'))
    component = relationship('Component')
    amount = Column(Float)


def save_scraped_data(scraped_recipes):
    engine = create_engine('sqlite:///factorio.db', echo=True)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    for scraped_recipe in scraped_recipes:
        print(scraped_recipe['time'])
        try:
            component = session.query(Component).filter(
                Component.name == scraped_recipe['output_name']).one()
        except NoResultFound:
            component = Component(name=scraped_recipe['output_name'])
            session.add(component)
        recipe = Recipe(
            time=scraped_recipe['time'],
            output=component,
            output_amount=scraped_recipe['output_amount']
        )
        session.add(recipe)
        for input in scraped_recipe['inputs']:
            try:
                component = session.query(Component).filter(
                    Component.name == input['name']).one()
            except NoResultFound:
                component = Component(name=input['name'])
            session.add(component)
            recipe_input = RecipeInput(
                component=component,
                recipe=recipe,
                amount=input['amount']
            )
            session.add(recipe_input)

    session.commit()
