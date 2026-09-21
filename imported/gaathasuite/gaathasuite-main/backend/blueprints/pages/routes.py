from flask import Blueprint, render_template

bp = Blueprint('pages', __name__)


@bp.route('/')
def index():
    return render_template('home.html')


@bp.route('/privacy')
def privacy():
    return render_template('privacy.html')


@bp.route('/user-agreement')
def user_agreement():
    return render_template('user_agreement.html')


@bp.route('/copyright')
def copyright():
    return render_template('copyright.html')


@bp.route('/about')
def about():
    return render_template('about.html')


@bp.route('/how-to-use')
def how_to_use():
    """A short guide for new users explaining where to find core features and how to get started."""
    return render_template('how_to_use.html')


@bp.route('/faqs')
def faqs():
    """FAQs page for basic common questions."""
    return render_template('faqs.html')


@bp.route('/overview')
def overview():
    """Gaatha Business Suite overview page."""
    return render_template('overview.html')


@bp.route('/features')
def features():
    """Features page showcasing all capabilities."""
    return render_template('features.html')
