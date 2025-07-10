# Plugin Marketplace

The plugin marketplace lets developers share and discover plugins for the Entity framework.

## Sharing Plugins
- Package your plugin with a standard `pyproject.toml` and upload it to the community registry.
- Include usage examples and a detailed description so others know what your plugin does.

## Installing from the Marketplace
- Use `pip install your-plugin` or future `entity-cli` commands to add a plugin to your project.
- Installed packages can then be referenced in your configuration just like local plugins.

## Rating and Reviews
- Marketplace users can rate plugins on a five-star scale and leave feedback.
- Ratings help highlight well-maintained plugins and signal potential issues.

## Searching the Marketplace
- A planned command `entity-cli search-plugin <name>` will query the registry and list matching plugins.
- The command will print each plugin's description and average rating.
