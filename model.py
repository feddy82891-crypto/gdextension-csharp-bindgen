from dataclasses import dataclass, field

@dataclass
class Api:
    classes: dict[str, Class] = field(default_factory=dict)
    
    def get_class(self, name: str) -> Class | None:
        return self.classes.get(name)

    def inheritance_chain(self, cls: Class) -> list[Class]:
        result = []

        if cls.inherits and cls.inherits in self.classes:
            inherited_class = self.classes[cls.inherits]
            result.append(inherited_class)

            result.extend(self.inheritance_chain(inherited_class))

        return result

    def get_all_methods(self, cls: Class) -> dict[str, Method]:
        result = dict(cls.methods)

        for inherited in self.inheritance_chain(cls):
            result.update(inherited.methods)

        return result

    def get_all_signals(self, cls: Class) -> dict[str, Signal]:
        result = dict(cls.signals)
        
        for inherited in self.inheritance_chain(cls):
            result.update(inherited.signals)
    
        return result

    def get_all_properties(self, cls: Class) -> dict[str, Property]:
        result = dict(cls.properties)
        
        for inherited in self.inheritance_chain(cls):
            result.update(inherited.properties)
    
        return result

@dataclass
class Argument:
    name: str = ""
    type: str = ""
    cs_type: str = ""
    meta: str = ""
    default_value: str = ""

@dataclass
class ReturnValue:
    type: str = ""
    cs_type: str = ""
    meta: str = ""

@dataclass
class Method:
    name: str = ""
    pascal_case_name: str = ""
    parent_class_name: str = ""
    hash: int = 0
    arguments: list[Argument] = field(default_factory=list)
    return_value: ReturnValue | None = None
    is_const: bool = False
    is_vararg: bool = False
    is_static: bool = False
    is_virtual: bool = False
    is_getter: bool = False

@dataclass
class Property:
    name: str = ""
    pascal_case_name: str = ""
    parent_class_name: str = ""
    type: str = ""
    cs_type: str = ""
    setter: str = ""
    getter: str = ""

@dataclass
class Signal:
    name: str = ""
    pascal_case_name: str = ""
    type: str = ""
    cs_type: str = ""
    arguments: list[Argument] = field(default_factory=list)

@dataclass
class Enum:
    name: str = ""
    value: int = 0

@dataclass
class Enums:
    name: str = ""
    is_bitfield: bool = False
    values: list[Enum] = field(default_factory=list)

@dataclass
class Class:
    name: str = ""
    is_refcounted: bool = False
    is_instantiable: bool = False
    inherits: str = ""
    api_type: str = ""
    
    methods: dict[str, Method] = field(default_factory=dict)
    signals: dict[str, Signal] = field(default_factory=dict)
    properties: dict[str, Property] = field(default_factory=dict)
    all_enums: dict[str, Enums] = field(default_factory=dict)
