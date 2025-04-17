from formaturas_app import create_app

app = create_app()

# Só roda se for executado diretamente (local)
if __name__ == '__main__':
    app.run(debug=True)
