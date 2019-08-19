from sqlalchemy import (
    create_engine, Column, Integer, String, Float, ForeignKey)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, aliased
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
    produced_by = Column(String)


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
    Base.metadata.create_all(engine)
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
        output_amount=scraped_recipe['output_amount'],
        produced_by=scraped_recipe['produced_by']
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
    for r in calculate_ratios():
        print(r.id, r.ratio, r.input, r.output)


def calculate_ratios():
    session = create_session(True)
    output_recipe = aliased(Recipe)
    input_recipe = aliased(Recipe)
    output_component = aliased(Component)
    input_component = aliased(Component)
    flows = (
        session.query(
            RecipeInput.id,
            (RecipeInput.amount / output_recipe.time * 60)
            .label('needed_per_min'),
            (input_recipe.output_amount / input_recipe.time * 60)
            .label('created_per_min'),
            output_component.name.label('output'),
            input_component.name.label('input'),
        )
        .join(output_recipe, output_recipe.id == RecipeInput.recipe_id)
        .join(input_recipe, input_recipe.output_id == RecipeInput.component_id)
        .join(output_component, output_component.id == output_recipe.output_id)
        .join(input_component, input_component.id == input_recipe.output_id)
        .subquery()
    )
    ratios = session.query(
        flows,
        (flows.c.needed_per_min / flows.c.created_per_min)
        .label('ratio')
    )
    return ratios


def input_ratio(session, recipe, input):
    needed_inputs_per_second = recipe.output_amount * input.amount / recipe.time
    input_recipe = session.query(Recipe).filter(
        Recipe.output_id == input.component_id).first()
    if not input_recipe:
        return 'No input recipe found'
    input_items_per_second = input_recipe.output_amount / input_recipe.time
    ratio = needed_inputs_per_second / input_items_per_second
    if input_recipe.produced_by != 'assembler':
        produced_by = ' ({})'.format(input_recipe.produced_by)
    else:
        produced_by = ''

    return '{:.2f}x {}{}'.format(
        ratio,
        input.component.name,
        produced_by,
    )
