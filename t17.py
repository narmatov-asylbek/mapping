from dataclasses import dataclass
from typing import List, Optional

from sqlalchemy.orm import registry, relationship, sessionmaker, composite, Session
from sqlalchemy import Column, Table, Integer, String, MetaData, ForeignKey, create_engine, event
from sqlalchemy.ext.mutable import MutableComposite


# path => src/collaboration/domain/model/value_objects/info.py ####
@dataclass                                                        #
class Info:                                                       #
    title: str                                                    #
    description: str                                              #
                                                                  #
    def concrete_method_1(self):                                  #
        # бизнес логика связанная с Info ...                      #
        ...                                                       #
                                                                  #
    def concrete_method_2(self):                                  #
        # бизнес логика связанная с Info ...                      #
        ...                                                       #
                                                                  #
###################################################################


# path => src/collaboration/domain/model/entities/topic.py #####################
class Topic:                                                                   #
                                                                               #
    def __init__(self, title: str, description: str):                          #
        self.title = title                                                     #
        self.description = description                                         #
                                                                               #
    def concrete_method_1(self):                                               #
        # бизнес логика связанная с Topic ...                                  #
        ...                                                                    #
                                                                               #
    def concrete_method_2(self):                                               #
        # бизнес логика связанная с Topic ...                                  #
        ...                                                                    #
                                                                               #
                                                                               #
# path => src/collaboration/domain/model/entities/stats.py                     #
class Stats:                                                                   #
                                                                               #
    def __init__(self, total_likes_count: int, total_comments_count: int):     #
        self.total_likes_count = total_likes_count                             #
        self.total_comments_count = total_comments_count                       #
                                                                               #
    def concrete_method_1(self):                                               #
        # бизнес логика связанная со Stats ...                                 #
        ...                                                                    #
                                                                               #
    def concrete_method_2(self):                                               #
        # бизнес логика связанная со Stats ...                                 #
        ...                                                                    #
                                                                               #
################################################################################


# path => src/collaboration/domain/model/aggregates/category.py #####################
class Category:                                                                     #
                                                                                    #
    def __init__(self, topics: List[Topic], info: Info, stats: Stats = None):       #
        self.topics = topics                                                        #
        self.info = info                                                            #
        self.stats = stats                                                          #
                                                                                    #
    def inc_like(self):                                                             #
        # централизованая бизнес логика ...                                         #
        self.stats.total_likes_count += 1

    def add_topic(self, topic: Topic):
        # до добавления выполняем контрактные ассерты
        self.topics.append(topic)
                                                                                    #
    def concrete_method_2(self):                                                    #
        # централизованая бизнес логика ...                                         #
        self.info.description.lower()    # какая то логика связаная с Info          #
                                                                                    #
    def concrete_method_3(self):                                                    #
        # централизованая бизнес логика ...                                         #
        str(self.stats.total_likes_count)    # какая то логика связаная со Stats    #
                                                                                    #
    def __eq__(self, other):                                                        #
        if not isinstance(other, type(self)):                                       #
            return False                                                            #
                                                                                    #
        return self.info == other.info                                              #
                                                                                    #
    def __hash__(self):                                                             #
        return hash(self.info.title) & hash(self.info.description)                  #
                                                                                    #
    def __repr__(self):                                                             #
        return f'Category(title={self.info.title})'                                 #
                                                                                    #
#####################################################################################


# path => /src/collaboration/infrastructure/persistence/sqlalchemy/mapping.py   ######################
mapper_registry = registry()                                                                         #
                                                                                                     #
categories = Table(                                                                                  #
    'categories', mapper_registry.metadata,                                                          #
    Column('id', Integer, primary_key=True),                                                         #
    Column('title', String(256)),                                                                    #
    Column('description', String(256)),                                                              #
    Column('total_likes_count', Integer, server_default='0'),                                        #
    Column('total_comments_count', Integer, server_default='0'),                                     #
)                                                                                                    #
                                                                                                     #
topics = Table(                                                                                      #
    'topics', mapper_registry.metadata,                                                              #
    Column('id', Integer, primary_key=True),                                                         #
    Column('title', String(256)),                                                                    #
    Column('description', String(256)),                                                              #
    Column('category_id', Integer, ForeignKey('categories.id')),                                     #
)                                                                                                    #
                                                                                                     #
                                                                                                     #
class InfoMix(Info):                                                                                 #
                                                                                                     #
    def __composite_values__(self):                                                                  #
        return self.title, self.description                                                          #
                                                                                                     #
                                                                                                     #
class StatsMix(MutableComposite, Stats):                                                             #
                                                                                                     #
    def __composite_values__(self):                                                                  #
        return self.total_likes_count, self.total_comments_count

    def __setattr__(self, key, value):
        "Intercept set events"

        # set the attribute
        object.__setattr__(self, key, value)

        # alert all parents to the change
        self.changed()

    def __eq__(self, other):
        return isinstance(other, StatsMix) and \
               other.total_likes_count == self.total_likes_count and \
               other.total_comments_count == self.total_comments_count

    def __ne__(self, other):
        return not self.__eq__(other)
                                                                                                     #
                                                                                                     #
topics_mapper = mapper_registry.map_imperatively(Topic, topics)                                      #
                                                                                                     #
mapper_registry.map_imperatively(                                                                    #
    Category, categories,                                                                            #
    properties={                                                                                     #
        'topics': relationship(                                                                      #
            topics_mapper,                                                                           #
        ),                                                                                           #
        'info': composite(                                                                           #
            InfoMix, 'title', 'description',                                                         #
        ),                                                                                           #
        'stats': composite(                                                                          #
            StatsMix, 'total_likes_count', 'total_comments_count',                                   #
        ),                                                                                           #
    }                                                                                                #
)                                                                                                    #
                                                                                                     #
######################################################################################################


# path => /src/collaboration/infrastructure/persistence/sqlalchemy/categories_repository.py ###########
class CategoriesRepository:                                                                           #
                                                                                                      #
    def __init__(self, session: Session):                                                             #
        self.session = session                                                                        #
                                                                                                      #
    def get_by_title(self, title: str):                                                               #
        return self.session.query(Category).filter_by(title=title).first()                            #
                                                                                                      #
    def create_category(self, title: str, description: str):                                          #
        new_category = Category(                                                                      #
            [], InfoMix(title, description),                                                          #
        )                                                                                             #
                                                                                                      #
        self.session.add(new_category)                                                                #
                                                                                                      #
        return new_category                                                                           #
                                                                                                      #
    def concrete_method_3(self):                                                                      #
        ...                                                                                           #
                                                                                                      #
    def concrete_method_4(self):                                                                      #
        ...                                                                                           #
                                                                                                      #
#######################################################################################################


engine = create_engine("sqlite:///:memory:", echo=True)
get_session = sessionmaker(bind=engine)
mapper_registry.metadata.create_all(engine)


with get_session() as session:
    repo = CategoriesRepository(session)
    new_category = repo.create_category('title 1', 'desc 1')
    session.commit()

with get_session() as session:
    repo = CategoriesRepository(session)

    category_from_repo = repo.get_by_title('title 1')
    print(category_from_repo)

    category_from_repo.inc_like()
    print(category_from_repo.stats.total_likes_count)

    new_topic = Topic('top title 1', 'top desc 1')
    category_from_repo.add_topic(new_topic)
    print(category_from_repo.topics)

    session.commit()
