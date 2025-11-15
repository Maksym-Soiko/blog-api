from django.core.management.base import BaseCommand
from django.apps import apps
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from django.db import IntegrityError
import random
import datetime

class Command(BaseCommand):
    def handle(self, *args, **options):
        fake = None
        try:
            from faker import Faker
            fake = Faker()
        except Exception:
            fake = None

        def gen_sentence():
            if fake:
                return fake.sentence(nb_words=6)
            words = ["lorem","ipsum","dolor","sit","amet","consectetur","adipiscing","elit","sed","do"]
            return " ".join(random.choices(words, k=8)).capitalize() + "."

        def gen_paragraph():
            if fake:
                return "\n\n".join(fake.paragraphs(nb=3))
            return "\n\n".join(gen_sentence() for _ in range(6))

        def get_model_by_names(names):
            for name in names:
                try:
                    return apps.get_model('blog', name)
                except LookupError:
                    continue
            return None

        AuthorModel = get_model_by_names(['Author', 'Profile'])
        if AuthorModel is None:
            try:
                AuthorModel = get_user_model()
            except Exception:
                AuthorModel = None

        CategoryModel = get_model_by_names(['Category', 'BlogCategory'])
        TagModel = get_model_by_names(['Tag', 'Label'])
        ArticleModel = get_model_by_names(['Article', 'Post', 'BlogPost'])
        CommentModel = get_model_by_names(['Comment', 'Feedback', 'PostComment'])

        created = {'authors': [], 'categories': [], 'tags': [], 'articles': [], 'comments': []}

        def create_instance(Model, defaults):
            if Model is None:
                return None
            try:
                if getattr(Model.objects, 'create_user', None):
                    u_kwargs = {}
                    if 'username' in defaults:
                        u_kwargs['username'] = defaults.get('username')
                    if 'email' in defaults:
                        u_kwargs['email'] = defaults.get('email')
                    password = defaults.pop('password', 'password123')
                    try:
                        return Model.objects.create_user(**u_kwargs, password=password)
                    except Exception:
                        return Model.objects.create(**{k: v for k, v in defaults.items() if k in [f.name for f in Model._meta.fields]})
                else:
                    valid = {f.name for f in Model._meta.fields}
                    create_kwargs = {k: v for k, v in defaults.items() if k in valid}
                    return Model.objects.create(**create_kwargs)
            except IntegrityError:
                lookup = {}
                if 'username' in defaults:
                    lookup['username'] = defaults['username']
                elif 'name' in defaults:
                    lookup['name'] = defaults['name']
                try:
                    return Model.objects.filter(**lookup).first()
                except Exception:
                    return Model.objects.first()
            except Exception:
                return None

        for i in range(3):
            name = f"Author {i+1}"
            username = f"author{i+1}"
            email = f"author{i+1}@example.com"
            defaults = {'name': name, 'username': username, 'email': email, 'password': 'pass1234'}
            author = create_instance(AuthorModel, defaults)
            if author:
                created['authors'].append(author)

        for i in range(5):
            title = f"Category {i+1}"
            slug = slugify(title)
            if CategoryModel:
                try:
                    obj = CategoryModel.objects.create(name=title) if 'name' in {f.name for f in CategoryModel._meta.fields} else CategoryModel.objects.create(title=title, slug=slug)
                except Exception:
                    obj = CategoryModel.objects.filter(name=title).first() or CategoryModel.objects.first()
                created['categories'].append(obj)

        for i in range(10):
            title = f"Tag{i+1}"
            if TagModel:
                try:
                    obj = TagModel.objects.create(name=title) if 'name' in {f.name for f in TagModel._meta.fields} else TagModel.objects.create(title=title)
                except Exception:
                    obj = TagModel.objects.filter(name=title).first() or TagModel.objects.first()
                created['tags'].append(obj)

        for i in range(20):
            title = f"Sample Article {i+1}"
            slug = slugify(title)
            body = gen_paragraph()
            author = random.choice(created['authors']) if created['authors'] else None
            category = random.choice(created['categories']) if created['categories'] else None
            if ArticleModel:
                try:
                    valid_fields = {f.name for f in ArticleModel._meta.fields}
                    kwargs = {}
                    if 'title' in valid_fields:
                        kwargs['title'] = title
                    if 'slug' in valid_fields:
                        kwargs['slug'] = slug
                    if 'body' in valid_fields:
                        kwargs['body'] = body
                    elif 'content' in valid_fields:
                        kwargs['content'] = body
                    if author:
                        for f in ArticleModel._meta.fields:
                            if getattr(f, 'remote_field', None) and f.remote_field.model == AuthorModel:
                                kwargs[f.name] = author
                                break
                    if category:
                        for f in ArticleModel._meta.fields:
                            if getattr(f, 'remote_field', None) and f.remote_field.model == CategoryModel:
                                kwargs[f.name] = category
                                break
                    article = ArticleModel.objects.create(**kwargs)
                    if created['tags']:
                        try:
                            if hasattr(article, 'tags'):
                                sample_tags = random.sample(created['tags'], k=min(3, len(created['tags'])))
                                article.tags.add(*sample_tags)
                            else:
                                for m in ArticleModel._meta.many_to_many:
                                    if m.related_model == TagModel or m.name.lower().find('tag') != -1:
                                        field = getattr(article, m.name)
                                        sample_tags = random.sample(created['tags'], k=min(3, len(created['tags'])))
                                        field.add(*sample_tags)
                                        break
                        except Exception:
                            pass
                    created['articles'].append(article)
                except Exception:
                    continue

        def find_fk_field_name(Model, target_model):
            for f in Model._meta.fields:
                if getattr(f, 'remote_field', None) and getattr(f.remote_field, 'model', None) == target_model:
                    return f.name
            for candidate in ('article', 'post', 'blogpost', 'object', 'entry'):
                if candidate in {f.name for f in Model._meta.fields}:
                    return candidate
            return None

        article_fk_name = find_fk_field_name(CommentModel, ArticleModel) if CommentModel and ArticleModel else None
        author_fk_name = find_fk_field_name(CommentModel, AuthorModel) if CommentModel and AuthorModel else None

        for i in range(50):
            body = gen_sentence()
            article = random.choice(created['articles']) if created['articles'] else None
            author = random.choice(created['authors']) if created['authors'] else None
            if CommentModel:
                try:
                    kwargs = {}
                    if article and article_fk_name:
                        kwargs[article_fk_name] = article
                    if author and author_fk_name:
                        kwargs[author_fk_name] = author
                    if 'text' in {f.name for f in CommentModel._meta.fields}:
                        kwargs['text'] = body
                    elif 'body' in {f.name for f in CommentModel._meta.fields}:
                        kwargs['body'] = body
                    elif 'message' in {f.name for f in CommentModel._meta.fields}:
                        kwargs['message'] = body
                    else:
                        for f in CommentModel._meta.fields:
                            if getattr(f, 'get_internal_type', None) and f.get_internal_type() in ('TextField', 'CharField'):
                                kwargs[f.name] = body
                                break
                    if 'created' in {f.name for f in CommentModel._meta.fields}:
                        kwargs['created'] = datetime.datetime.now()
                    comment = CommentModel.objects.create(**kwargs)
                    created['comments'].append(comment)
                except Exception:
                    continue

        self.stdout.write(self.style.SUCCESS(
            f"Created: authors={len(created['authors'])}, categories={len(created['categories'])}, "
            f"tags={len(created['tags'])}, articles={len(created['articles'])}, comments={len(created['comments'])}"
        ))