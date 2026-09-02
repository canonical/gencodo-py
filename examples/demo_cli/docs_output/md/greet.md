# greet

Greet a specific person

**Usage:**

```
democli greet [--formal] [--enthusiasm ENTHUSIASM] [--suffix SUFFIX] name
```

## Overview

The greet command allows you to personalize your greeting by specifying
a name. You can also customize the greeting style and add an optional
message suffix.

This command demonstrates how to use positional and optional arguments.

## Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `name` | Name of the person to greet |  |

## Options

| Flag | Description | Default |
|------|-------------|---------|
| `--formal` | Use formal greeting style |  |
| `--enthusiasm` | Enthusiasm level (1-5) | `1` |
| `--suffix` | Optional message suffix |  |

## Examples

**Greet Alice**

```
democli greet Alice
```

**Greet Bob formally**

```
democli greet Bob --formal
```

**Greet Charlie with enthusiasm**

```
democli greet Charlie --enthusiasm 5
```

**Greet with a suffix**

```
democli greet Alice --suffix ', have a great day!'
```

## See also

- [farewell](farewell.md)
- [hello](hello.md)
