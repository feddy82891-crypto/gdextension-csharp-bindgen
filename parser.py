import model
import resolver
import helper

IGNORED_METHODS = [
    "to_string",
    "setup_local_to_scene",
    "_setup_local_to_scene",
    "copy_from_resource"
]

class ApiParser:
    type_resolver: resolver.TypeResolver | None = None

    def parse(self, raw_api: dict) -> model.Api:
        api = model.Api()

        self.type_resolver = resolver.TypeResolver(raw_api, api)

        self.parse_classes(raw_api, api)

        return api

    def find_raw_class(self, raw_api: dict, class_name: str):
        for raw_class in raw_api.get("classes", {}):
            if raw_class.get("name") == class_name:
                return raw_class

    def parse_property(self, raw_property, class_name: str) -> model.Property:
        property = model.Property()
        property.name = raw_property.get("name", "")
        property.pascal_case_name = helper.to_pascal_case(property.name)
        property.parent_class_name = class_name
        property.type = raw_property.get("type", "")
        property.setter = raw_property.get("setter", "")
        property.getter = raw_property.get("getter", "")

        return property

    def parse_arguments(self, raw_arguments) -> list[model.Argument]:
        if raw_arguments is None:
            return []

        argument_list: list[model.Argument] = []

        for raw_argument in raw_arguments:
            argument = model.Argument(
                name='@' + raw_argument.get("name", ""),
                type=raw_argument.get("type", ""),
                meta=raw_argument.get("meta", ""),
                default_value=raw_argument.get("default_value", "")
            )

            resolved_argument = self.type_resolver.resolve_argument(argument)

            argument_list.append(resolved_argument)

        return argument_list

    def parse_return_value(self, raw_return_value) -> model.ReturnValue | None:
        if raw_return_value is None:
            return None

        return_value: model.ReturnValue = model.ReturnValue()
        return_value.type = raw_return_value.get("type", "")
        return_value.meta = raw_return_value.get("meta", "")

        return return_value

    def parse_method(self, raw_method, class_name: str) -> model.Method:
        return model.Method(
            name=raw_method.get("name", ""),
            pascal_case_name = helper.to_pascal_case(raw_method.get("name", "")),
            parent_class_name=class_name,
            is_const=raw_method.get("is_const", False),
            is_vararg=raw_method.get("is_vararg", False),
            is_static=raw_method.get("is_static", False),
            is_virtual=raw_method.get("is_virtual", False),
            hash=raw_method.get("hash", 0),
            arguments=self.parse_arguments(raw_method.get("arguments", [])),
            return_value=self.parse_return_value(raw_method.get("return_value"))
        )

    def parse_signal(self, raw_signal) -> model.Signal:
        return model.Signal(
            name=raw_signal.get("name", ""),
            pascal_case_name = helper.to_pascal_case(raw_signal.get("name", "")),
            type=raw_signal.get("type", ""),
            arguments=self.parse_arguments(raw_signal.get("arguments", []))
        )

    def parse_enum(self, raw_enum) -> model.Enum:
        return model.Enum(
            name=raw_enum.get("name", ""),
            value=raw_enum.get("value", 0)
        )

    def parse_enums(self, raw_enums) -> model.Enums:
        values = []

        for value in raw_enums.get("values", []):
            values.append(self.parse_enum(value))

        return model.Enums(
            name=raw_enums.get("name", ""),
            is_bitfield=raw_enums.get("is_bitfield", False),
            values=values
        )

    def parse_class(self, raw_api: dict, api: model.Api, raw_class: dict):
        if raw_class is None:
            return

        class_name = self.type_resolver.resolve_type_name(raw_class.get("name", ""))
        inherits = self.type_resolver.resolve_type_name(raw_class.get("inherits", ""))

        if inherits:
            self.parse_class(raw_api, api, self.find_raw_class(raw_api, raw_class.get("inherits", "")))
        
        if api.get_class(class_name):
            return

        cls = model.Class(
            name=class_name,
            is_refcounted=raw_class.get("is_refcounted", False),
            is_instantiable=raw_class.get("is_instantiable", False),
            inherits=inherits,
            api_type=raw_class.get("api_type", "")
        )

        for raw_method in raw_class.get("methods", []):
            if raw_method.get("name") in IGNORED_METHODS:
                continue

            parsed_method: model.Method = self.parse_method(raw_method, cls.name)
            cls.methods[parsed_method.name] = self.type_resolver.resolve_method(parsed_method)

        for raw_property in raw_class.get("properties", []):
            parsed_property: model.Property = self.parse_property(raw_property, cls.name)
            resolved_property: model.Property = self.type_resolver.resolve_property(parsed_property, cls.methods)
            cls.properties[parsed_property.name] = resolved_property

        for raw_signal in raw_class.get("signals", []):
            parsed_signal: model.Signal = self.parse_signal(raw_signal)
            resolved_signal: model.Signal = self.type_resolver.resolve_signal(parsed_signal)
            cls.signals[parsed_signal.name] = resolved_signal

        for raw_enums in raw_class.get("enums", []):
            parsed_enums: model.Enums = self.parse_enums(raw_enums)
            cls.all_enums[parsed_enums.name] = parsed_enums

        api.classes[cls.name] = cls

        return cls

    def parse_classes(self, raw_api: dict, api: model.Api):
        for raw_class in raw_api.get("classes", []):
            if raw_class.get("api_type") == "extension":
                self.parse_class(raw_api, api, raw_class)