import model
import helper

TYPE_NAME_MAP = {
    "RID": "Rid",
    "AABB": "Aabb",
    "MultiplayerAPI": "MultiplayerApi",
    "Object": "GodotObject",
    "Vector2i": "Vector2I",
    "Vector3i": "Vector3I"
}

META_MAP = {
    "int32": "int",
    "int64": "long",
    "uint32": "uint",
    "uint64": "ulong",
    "float": "float",
    "double": "double"
}

NUMERIC_TYPES = [
    "int",
    "uint",
    "short",
    "ushort",
    "long",
    "ulong",
    "double",
    "float"
]

STRING_TYPES = [
    "string",
    "String"
]

class TypeResolver:
    raw_api: dict | None = None
    api: model.Api | None = None

    array_types: set[str] = None

    builtin_types: set[str] = None
    raw_classes: dict = None

    def __init__(self, raw_api: dict, api: model.Api):
        self.raw_api = raw_api
        self.api = api

        self.builtin_types = set()
        self.raw_classes = dict()

        self.get_builtin_types(raw_api)

        self.raw_classes = {
            cls["name"]: cls
            for cls in raw_api.get("classes", {})
        }
    
    def get_builtin_types(self, raw_api: dict):
        for cls in raw_api.get("builtin_classes", {}):
            name = self.resolve_type_name(cls.get("name"))

            if name not in NUMERIC_TYPES and name not in STRING_TYPES:
                self.builtin_types.add(name)

    def get_raw_class(self, class_name: str) -> dict:
        return self.raw_classes.get(class_name)
    
    def inheritance_chain(self, class_name: str) -> list[str]:
        result = []
        current = class_name

        while True:
            raw_class = self.get_raw_class(current)

            if not raw_class:
                break
            
            parent = raw_class.get("inherits")

            result.append(parent)
            current = parent

        return result

    # API property names use snake_case, while property_name uses PascalCase.
    # Convert the property name so both values use the same naming convention. 
    def has_property(self, class_name: str, property_name: str) -> bool:
        raw_class = self.raw_classes.get(class_name)

        if raw_class is None:
            return False

        for raw_property in raw_class.get("properties", []):
            name = helper.to_pascal_case(raw_property.get("name", ""))

            if name == property_name:
                return True

        return False

    def is_getter(self, method: model.Method) -> bool:
        raw_class = self.raw_classes.get(method.parent_class_name)

        if raw_class is None:
            return False

        for raw_property in raw_class.get("properties", []):
            if raw_property.get("getter") == method.name:
                return True

        return False

    def is_builtin_type(self, type_name: str) -> bool:
        return type_name in self.builtin_types

    def is_numeric(self, type_name: str) -> bool:
        return type_name in NUMERIC_TYPES or type_name in META_MAP

    def is_string(self, type_name: str) -> bool:
        return type_name in STRING_TYPES

    def is_bool(self, type_name: str) -> bool:
        return type_name == "bool"

    def is_enum(self, type_name: str) -> bool:
        return "enum::" in type_name or "bitfield::" in type_name

    def is_resource(self, type_name: str) -> bool:
        return "Resource" in self.inheritance_chain(type_name)

    def is_node(self, type_name: str) -> bool:
        return "Node" in self.inheritance_chain(type_name)

    def is_array(self, type_name: str) -> bool:
        return "typedarray::" in type_name or "Array" == type_name

    def is_packed_array(self, type_name: str) -> bool:
        return type_name.startswith("Packed") and type_name.endswith("Array")

    def is_dictionary(self, type_name: str) -> bool:
        return "typeddictionary::" in type_name or type_name == "Dictionary"

    def resolve_numeric_type(self, meta_name: str, type_name: str) -> str:
        return META_MAP.get(meta_name, type_name) or META_MAP.get(type_name, type_name)

    def resolve_enum_type(self, type_name: str) -> str:
        _, _, enum_type = type_name.partition("::")

        class_name, _, enum_name = enum_type.partition(".")

        if self.has_property(class_name, enum_name):
            return enum_type + "Enum"

        return enum_type

    def resolve_packed_array_type(self, type_name: str) -> str:
        inner_type = type_name.removeprefix("Packed").removesuffix("Array")

        if self.is_numeric(inner_type.lower()) or self.is_string(inner_type.lower()):
            inner_type = inner_type.lower()

        inner_type = self.resolve_type(inner_type, inner_type)

        return f"{inner_type}[]"

    def resolve_array_type(self, type_name: str) -> str:
        _, _, tvalue = type_name.partition("::")

        result = "Godot.Collections.Array"

        tvalue = self.resolve_type(tvalue)

        if tvalue == "":
            return result
        else:
            return f"{result}<{tvalue}>"

    def resolve_dictionary_type(self, type_name: str) -> str:
        _, _, dictionary_type = type_name.partition("::")

        tkey, _, tvalue = dictionary_type.partition(";")

        tvalue = self.resolve_type(tvalue)

        result = "Godot.Collections.Dictionary"

        if dictionary_type == "":
            return result
        else:
            return f"{result}<{tkey}, {tvalue}>"

    def resolve_builtin_type(self, type_name: str) -> str:
        return f"Godot.{type_name}"

    def resolve_type_name(self, type_name: str) -> str:
        return TYPE_NAME_MAP.get(type_name, type_name)

    def resolve_type(self, type_name: str, meta_name: str = None) -> str:
        type_name = self.resolve_type_name(type_name)
        
        if self.is_numeric(type_name) and meta_name is not None:
            return self.resolve_numeric_type(meta_name, type_name)
        elif self.is_string(type_name):
            return "string"
        elif self.is_enum(type_name):
            return self.resolve_enum_type(type_name)
        elif self.is_array(type_name):
            return self.resolve_array_type(type_name)
        elif self.is_packed_array(type_name):
            return self.resolve_packed_array_type(type_name)
        elif self.is_dictionary(type_name):
            return self.resolve_dictionary_type(type_name)

        return type_name

    def resolve_default_value(self, argument: model.Argument) -> str:
        default = argument.default_value

        if default == "":
            return ""

        if self.is_enum(argument.type):
            return f"({argument.cs_type}){default}"

        if self.is_numeric(argument.type):
            return f"({argument.cs_type}){default}"

        if self.is_string(argument.type):
            return '""'

        if self.is_bool(argument.type):
            return "false"

        if self.is_array(argument.type):
            if argument.cs_type == "Godot.Collections.Array":
                return "default"

            return f"new {argument.cs_type}()"

        if self.is_dictionary(argument.type):
            if argument.cs_type == "Godot.Collections.Dictionary":
                return "default"

            return f"new {argument.cs_type}()"

        if self.is_builtin_type(argument.type):
            return "default"

        if argument.type == "Variant":
            return "default"

        return default
        
    def resolve_argument(self, argument: model.Argument) -> model.Argument:
        argument.cs_type = self.resolve_type(argument.type, argument.meta)

        argument.default_value = self.resolve_default_value(argument)
        
        return argument

    def resolve_property(self, prop: model.Property, methods: dict[str, model.Method]) -> model.Property:
        getter = methods.get(prop.getter)

        if getter is None:
            prop.cs_type = prop.type
            return prop

        prop.cs_type = self.resolve_type(getter.return_value.type, getter.return_value.meta)

        return prop

    def resolve_method(self, method: model.Method) -> model.Method:
        if method.return_value is None:
            return method

        if not self.is_enum(method.return_value.type):
            method.is_getter = self.is_getter(method)

        method.return_value.cs_type = self.resolve_type(method.return_value.type, method.return_value.meta)

        return method

    def resolve_signal(self, signal: model.Signal) -> model.Signal:
        if not signal.arguments:
            signal.cs_type = ""
            
            return signal

        argument_types = [
            self.resolve_type(argument.type)
            for argument in signal.arguments
        ]

        signal.cs_type = f"<{', '.join(argument_types)}>"

        return signal