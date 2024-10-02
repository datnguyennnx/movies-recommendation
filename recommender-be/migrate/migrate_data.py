import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Movie, Genre, Actor, Director, Base
from config.settings import settings
import json
import ast
import traceback

# Initialize SQLAlchemy engine and session
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)

def parse_list(s):
    try:
        return ast.literal_eval(s)
    except:
        return []

def migrate_data():
    # Read CSV files
    movies_df = pd.read_csv('data/tmdb_5000_movies.csv')
    credits_df = pd.read_csv('data/tmdb_5000_credits.csv')

    # Merge dataframes
    df = pd.merge(movies_df, credits_df, left_on='id', right_on='movie_id')
    
    # Rename columns to avoid conflicts
    df = df.rename(columns={'title_x': 'title'})

    session = SessionLocal()

    try:
        for index, row in df.iterrows():
            try:
                # Create Movie instance
                movie = Movie(
                    id=row.get('id'),
                    title=row.get('title', ''),
                    budget=row.get('budget', 0),
                    genres_data=json.dumps(parse_list(row.get('genres', '[]'))),
                    homepage=row.get('homepage', ''),
                    keywords=json.dumps(parse_list(row.get('keywords', '[]'))),
                    original_language=row.get('original_language', ''),
                    original_title=row.get('original_title', ''),
                    overview=row.get('overview', ''),
                    popularity=row.get('popularity', 0.0),
                    production_companies=json.dumps(parse_list(row.get('production_companies', '[]'))),
                    release_date=row.get('release_date', ''),
                    revenue=row.get('revenue', 0),
                    runtime=row.get('runtime', 0),
                    status=row.get('status', 'Unknown'),
                    tagline=row.get('tagline', ''),
                    vote_average=row.get('vote_average', 0.0),
                    vote_count=row.get('vote_count', 0),
                    cast=json.dumps(parse_list(row.get('cast', '[]'))),
                    crew=json.dumps(parse_list(row.get('crew', '[]')))
                )

                # Add genres
                genres = parse_list(row.get('genres', '[]'))
                for genre_data in genres:
                    genre = session.query(Genre).filter_by(name=genre_data['name']).first()
                    if not genre:
                        genre = Genre(name=genre_data['name'])
                    movie.genres.append(genre)

                # Add director
                crew = parse_list(row.get('crew', '[]'))
                director_data = next((item for item in crew if item["job"] == "Director"), None)
                if director_data:
                    director = session.query(Director).filter_by(name=director_data['name']).first()
                    if not director:
                        director = Director(name=director_data['name'])
                        session.add(director)
                        session.flush()  # This will assign an ID to the director
                    movie.director_id = director.id

                # Add actors (top 3)
                cast = parse_list(row.get('cast', '[]'))[:3]
                for actor_data in cast:
                    actor = session.query(Actor).filter_by(name=actor_data['name']).first()
                    if not actor:
                        actor = Actor(name=actor_data['name'])
                    movie.actors.append(actor)

                session.add(movie)

                if index % 100 == 0:
                    session.commit()
                    print(f"Processed {index} movies")

            except Exception as e:
                print(f"Error processing movie at index {index}: {str(e)}")
                print(f"Problematic row: {row}")
                traceback.print_exc()
                session.rollback()

        session.commit()
        print("Data migration completed successfully.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        traceback.print_exc()
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    migrate_data()