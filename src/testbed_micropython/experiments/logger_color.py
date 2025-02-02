import click

# from click.termui import style as style


def main() -> None:
    click.echo(click.style("Hello World!", fg="green", dim=False))
    click.echo(click.style("Hello World!", fg="green", bold=True))
    click.echo(click.style("Hello World!", fg="green", dim=True))
    click.echo(click.style("Hello World!", fg="green", dim=True, reverse=True))


if __name__ == "__main__":
    main()
