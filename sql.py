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


def run_schema_creation():
    engine = create_engine('sqlite:///factorio.db')
    Base.metadata.create_all(engine)


def create_session(echo=True):
    engine = create_engine('sqlite:///factorio.db', echo=echo)
    Session = sessionmaker(bind=engine)
    session = Session()
    return session


def save_scraped_recipe(scraped_recipe):
    session = create_session(False)
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


def show_assembler_ratios():
    print("This list shows how many assemblers you need for each input component to fully supply an assembler producing some component.")
    session = create_session(False)
    for component in session.query(Component).order_by(Component.name):
        print('{}'.format(
            component.name))
        recipe = session.query(Recipe)\
            .filter(Recipe.output_id == component.id).first()
        if not recipe:
            print("    Nothing!")
            continue
        inputs = session.query(RecipeInput)\
            .filter(RecipeInput.recipe_id == recipe.id)
        for input in inputs:
            print('    ' + input_ratio(session, recipe, input))


def input_ratio(session, recipe, input):
    needed_inputs_per_second = recipe.output_amount * input.amount / recipe.time
    input_recipe = session.query(Recipe).filter(
        Recipe.output_id == input.component_id).first()
    if not input_recipe:
        return 'No input recipe found'
    input_items_per_second = input_recipe.output_amount / input_recipe.time
    ratio = needed_inputs_per_second / input_items_per_second
    return '{:.2f}x {}'.format(
                ratio, input.component.name)
