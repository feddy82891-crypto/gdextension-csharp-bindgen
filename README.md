# GDExtension C# Bindings Generator

Generates C# bindings for GDExtension classes.

Successfully tested with Godot 4.6.3.

## About

This tool generates C# bindings for classes provided by GDExtension.

The general concept was inspired by the existing Godot add-on by [gilzoide](https://github.com/gilzoide) called [godot-csharp-gdextension-bindgen](https://github.com/gilzoide/godot-csharp-gdextension-bindgen). However, this tool uses a different implementation and fixes several type resolution, type casting, and other issues.

## Usage

1. Generate an Extension API dump with your GDExtension loaded:

```bash
godot --headless --dump-extension-api path_to_your_project_directory
```

2. Run `main.py`.

The default API file path can be used, or you can specify a custom path:

```bash
python3 main.py
```

```bash
python3 main.py path_to_api_file
```

Python 3 is required.

## How it works

The tool parses the Extension API file into Python objects, resolves and converts Godot API types into their corresponding C# representations, and generates C# source code by loading templates and replacing placeholders with the generated values.