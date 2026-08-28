from pathlib import Path

import model

import os
import re

TEMPLATES_DIR = Path(__file__).parent / "templates"

def load_template(name: str) -> str:
    path = TEMPLATES_DIR / f"{name}.txt"

    if not path.exists():
        raise FileNotFoundError(
            f"Template not found: {path}"
        )

    return path.read_text(encoding="utf-8")

class CSharpBindingGenerator():
    api: model.Api = None

    PLACEHOLDER_PATTERN = re.compile(r"([ \t]*)%([A-Z_]+)%")
    
    def __init__(self, api_obj: model.Api):
        self.api = api_obj

    def render(self, template: str, values: dict[str, str]) -> str:
        def replace(match: re.Match) -> str:
            indent = match.group(1)
            key = match.group(2)

            if key not in values:
                raise ValueError(
                    f"Unknown placeholder: %{key}%"
                )

            value = values[key]
            
            if not value:
                return ""

            lines = value.splitlines()
            
            return indent + f"\n{indent}".join(lines)

        return self.PLACEHOLDER_PATTERN.sub(replace, template)

    def generate_enums(self, enums: model.Enums) -> str:
        result = []

        for enum in enums.values:
            result.append(f"{enum.name} = {enum.value}")

        return self.render(
            load_template("enums"),
            {
                "NAME": enums.name,
                "ENUMS": ', \n'.join(result)
            }
        )

    def generate_all_enums(self, cls: model.Class) -> str:
        result = []

        for enums in cls.all_enums.values():
            result.append(self.generate_enums(enums))

        return '\n'.join(result)

    def generate_property_names(self, cls: model.Class) -> str:
        names = []

        for prop in cls.properties.values():
            names.append(self.render(
                load_template("string_name"),
                {
                    "NAME": prop.name,
                    "PASCAL_NAME": prop.pascal_case_name
                }
            ))

        return self.render(
                load_template("property_class"),
                {
                    "INHERITS": cls.inherits,
                    "PROPERTY_NAMES": "\n".join(names)
                }
            )

    def generate_method_names(self, cls: model.Class) -> str:
        names = []

        for method in cls.methods.values():
            names.append(self.render( 
                load_template("string_name"),
                {
                    "NAME": method.name,
                    "PASCAL_NAME": method.pascal_case_name
                }
            ))

        return self.render(
                load_template("method_class"),
                {
                    "INHERITS": cls.inherits,
                    "METHOD_NAMES": "\n".join(names)
                }
            )

    def generate_signal_names(self, cls: model.Class) -> str:
        names = []

        for signal in cls.signals.values():
            names.append(self.render(
                load_template("string_name"),
                {
                    "NAME": signal.name,
                    "PASCAL_NAME": signal.pascal_case_name
                }
            ))

        return self.render(
                load_template("signal_class"),
                {
                    "INHERITS": cls.inherits,
                    "SIGNAL_NAMES": "\n".join(names)
                }
            )

    def generate_property(self, property: model.Property, cls: model.Class) -> str:
        inherited = (property.parent_class_name != cls.name)

        property_template = "inherited_property" if inherited else "property"

        setter = ""
        read_only = (property.setter == "")

        if not read_only:
            if inherited:
                setter = f"set => _object.{property.pascal_case_name} = value;"
            else:
                setter = f"set => _object.Set(PropertyName.{property.pascal_case_name}, value);"

        return self.render(
            load_template(property_template),
            {
                "PASCAL_NAME": property.pascal_case_name,
                "TYPE": property.cs_type,
                "SETTER": setter
            }
        )

    def generate_properties(self, cls: model.Class) -> str:
        result = []

        for prop in self.api.get_all_properties(cls).values():
            result.append(self.generate_property(prop, cls))

        return '\n'.join(result)

    def generate_argument(self, argument: model.Argument, only_names: bool = False) -> str:
        result = ""

        if only_names:
            result = argument.name
        else:
            result = f"{argument.cs_type} {argument.name}"

            if argument.default_value:
                result += f" = {argument.default_value}"

        return result
        
    def generate_arguments(self, arguments: list[model.Argument], only_names: bool, is_vararg: bool) -> str:
        args = []

        for argument in arguments:
            args.append(self.generate_argument(argument, only_names))

        result = ', '.join(args)

        if is_vararg and not only_names:
            result += ", params Variant[] @varargs"

        return result
        
    def generate_method(self, method: model.Method) -> str:
        return_value = "void"
        returns = ""

        arguments = ""
        argument_names = ""

        if method.arguments:
            arguments = self.generate_arguments(method.arguments, False, method.is_vararg)
            argument_names = f", {self.generate_arguments(method.arguments, True, method.is_vararg)}"

        if method.return_value:
            return_value = "Godot.Variant"
            returns = "return"

        return self.render(
            load_template("method"),
            {
                "PASCAL_NAME": method.pascal_case_name,
                "ARGUMENTS": arguments,
                "ARGUMENT_NAMES": argument_names,
                "RETURN_VALUE": return_value,
                "RETURN": returns
            }
        )

    def generate_inherited_method(self, method: model.Method) -> str:
        return_value = "void"
        returns = ""

        arguments = ""
        argument_names = ""

        if method.arguments:
            arguments = self.generate_arguments(method.arguments, False, method.is_vararg)
            argument_names = self.generate_arguments(method.arguments, True, method.is_vararg)

        if method.return_value:
            return_value = "Godot.Variant" if method.is_getter else method.return_value.cs_type
            returns = "return"

        return self.render(
            load_template("inherited_method"),
            {
                "PASCAL_NAME": method.pascal_case_name,
                "ARGUMENTS": arguments,
                "ARGUMENT_NAMES": argument_names,
                "RETURN_VALUE": return_value,
                "RETURN": returns
            }
        )

    def generate_static_method(self, method: model.Method) -> str: 
        return_value = "void"
        returns = ""

        arguments = ""
        argument_names = ""

        if method.arguments:
            arguments = self.generate_arguments(method.arguments, False, method.is_vararg)
            argument_names = self.generate_arguments(method.arguments, True, method.is_vararg)

        if method.return_value:
            return_value = "Godot.Variant" if method.is_getter else method.return_value.cs_type
            returns = "return"

        return self.render(
            load_template("static_method"),
            {
                "PASCAL_NAME": method.pascal_case_name,
                "ARGUMENTS": arguments,
                "ARGUMENT_NAMES": argument_names,
                "RETURN_VALUE": return_value,
                "RETURN": returns,
                "PARENT_CLASS_NAME": method.parent_class_name
            }
        )

    def generate_methods(self, cls: model.Class) -> str:
        result = []

        for method in self.api.get_all_methods(cls).values():
            is_inherited = (method.parent_class_name != cls.name)

            if method.is_static:
                result.append(self.generate_static_method(method))
            elif is_inherited:
                result.append(self.generate_inherited_method(method))
            else:
                result.append(self.generate_method(method))
            
        return '\n\n'.join(result)

    def generate_signal(self, signal: model.Signal) -> str:
        return self.render(
            load_template("signal"),
            {
                "PASCAL_NAME": signal.pascal_case_name,
                "INNER_TYPE": signal.cs_type
            }
        )
    
    def generate_signals(self, cls: model.Class) -> str:
        result = []

        for signal in self.api.get_all_signals(cls).values():
            result.append(self.generate_signal(signal))

        return '\n\n'.join(result)

    def generate_class(self, cls: model.Class):
        with open("bindings/" + cls.name + ".cs", "w", encoding="utf-8") as file:
            result = self.render(
                load_template("class"),
                {
                    "NAME": cls.name,
                    "INHERITS": cls.inherits,
                    "ENUMS": self.generate_all_enums(cls),
                    "PROPERTY_NAMES": self.generate_property_names(cls),
                    "METHOD_NAMES": self.generate_method_names(cls),
                    "SIGNAL_NAMES": self.generate_signal_names(cls),
                    "PROPERTIES": self.generate_properties(cls),
                    "METHODS": self.generate_methods(cls),
                    "SIGNALS": self.generate_signals(cls)
                }
            )

            file.write(result)
            file.close()

    def generate_classes(self):
        os.makedirs("bindings", exist_ok=True)
        
        for extension_class in self.api.classes.values():
            if extension_class.api_type == "extension":
                self.generate_class(extension_class)
