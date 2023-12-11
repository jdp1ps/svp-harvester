import TomSelect from "tom-select";

class TextFieldSelector {

    constructor(rootElementSelector, plugins = []) {
        const defaultPlugins = ['checkbox_options', 'remove_button', 'clear_button']

        // Combine default plugins and provided plugins, removing any duplicates.
        const allPlugins = [...new Set([...defaultPlugins, ...plugins])];

        this.selector = new TomSelect(rootElementSelector, {
            sortField: {field: "text"},
            plugins: allPlugins,
        });
    }

    getValue() {
        return [].concat(this.selector.getValue());
    }
}

export default TextFieldSelector;
