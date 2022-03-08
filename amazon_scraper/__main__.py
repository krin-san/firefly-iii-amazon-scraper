import argparse
import logging
import pkgutil
import sys

from dotenv import dotenv_values

from amazon_scraper import actions
from amazon_scraper.amazon.scraper import AmazonScraper
from amazon_scraper.deps import AppArgs, Runner
from amazon_scraper.firefly.api import FireflyAPI


def setup_env():
    env = dotenv_values()

    REQUIRED_ENV_VARS = {
        "AMAZON_HOST", "AMAZON_USER", "AMAZON_PASSWORD",
        "FIREFLY_HOST", "FIREFLY_TOKEN",
    }
    env_diff = REQUIRED_ENV_VARS.difference(env)
    if len(env_diff) > 0:
        raise EnvironmentError(f'Failed because {list(env_diff)} are not set')

    return env

def setup_parser(is_cli: bool):
    parser = argparse.ArgumentParser(
        prog="python -m amazon_scraper",
        description="Scrape an Amazon account and create order PDFs."
    )
    parser.add_argument(
        "--cache_dir",
        required=False,
        default=".cache/",
        help='Cache directory for fetched web pages and scraped order details. Defaults to ".cache/"',
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run in read-only mode, without changing any data in Firefly III database.",
    )
    parser.add_argument(
        "--log",
        help="Filename for storing all logging messages. Logs to stdout by default.",
    )
    parser.add_argument(
        "--log-level",
        help="Log level. Not set by default, logging all produced messages.",
    )

    subparsers = parser.add_subparsers(title="command", dest="command", required=is_cli)
    for importer, modname, _ in pkgutil.iter_modules(actions.__path__):
        if modname == "common":
            continue
        module = importer.find_spec(modname).loader.load_module(modname)
        subparser = subparsers.add_parser(modname, help=module.__doc__)
        subparser.set_defaults(func=module.run)

    return parser

def setup_logger(args: AppArgs):
    logger = logging.getLogger()

    if (filename := args.log):
        logger.addHandler(logging.FileHandler(filename))
    else:
        logger.addHandler(logging.StreamHandler(sys.stdout))

    if (level := args.log_level):
        logger.setLevel(getattr(logging, level.upper()))
    else:
        logger.setLevel(logging.NOTSET)

def setup(is_cli: bool = True, args = None):
    env = setup_env()
    parser = setup_parser(is_cli)
    args = parser.parse_args(args)
    app_args = AppArgs(args)
    setup_logger(app_args)
    amazon = AmazonScraper(
        host=env["AMAZON_HOST"],
        user=env["AMAZON_USER"],
        password=env["AMAZON_PASSWORD"],
        cache_dir=app_args.cache_dir,
    )
    firefly = FireflyAPI(
        host=env["FIREFLY_HOST"],
        auth_token=env["FIREFLY_TOKEN"],
    )
    return (args, Runner(amazon, firefly, app_args))

def main():
    (args, runner) = setup()
    args.func(runner)

if __name__ == "__main__":
    main()
