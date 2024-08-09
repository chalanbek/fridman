SCgComponent = {
    ext_lang: 'scg_code',
    formats: ['format_scg_json'],
    struct_support: true,
    factory: function (sandbox) {
        return new SCgViewerWindow(sandbox);
    }
};


/**
 * SCgViewerWindow
 * @param sandbox
 * @constructor
 */
const SCgViewerWindow = function (sandbox) {
    const self = this;

    this.sandbox = sandbox;
    this.tree = new SCg.Tree();
    this.editor = new SCg.Editor();

    if (sandbox.is_struct) {
        this.scStructTranslator = new SCgStructTranslator(this.editor, this.sandbox);
    }

    const autocompletionVariants = function (keyword, callback) {
        window.scClient.getLinksContentsByContentSubstrings([keyword]).then((strings) => {
            const maxContentSize = 80;
            const keys = strings.length ? strings[0].filter((string) => string.length < maxContentSize) : [];
            callback(keys);
        });
    };

    this.editor.init(
        {
            sandbox: sandbox,
            containerId: sandbox.container,
            autocompletionVariants: autocompletionVariants,
            translateToSc: function (callback) {
                return self.scStructTranslator.translateToSc().then(callback).catch(callback);
            },
            canEdit: this.sandbox.canEdit(),
            resolveControls: this.sandbox.resolveElementsAddr,
        }
    );


    this.receiveData = function (data) {
        this._buildGraph(data);
    };

    this._buildGraph = function (data) {
        var elements = {};
        var edges = [];
        for (var i = 0; i < data.length; i++) {
            var el = data[i];

            if (elements.hasOwnProperty(el.id))
                continue;
            if (Object.prototype.hasOwnProperty.call(this.editor.scene.objects, el.id)) {
                elements[el.id] = this.editor.scene.objects[el.id];
                continue;
            }

            if (el.el_type & sc_type_node || el.el_type & sc_type_link) {
                var model_node = SCg.Creator.createNode(el.el_type, new SCg.Vector3(10 * Math.random(), 10 * Math.random(), 0), '');
                this.editor.scene.appendNode(model_node);
                this.editor.scene.objects[el.id] = model_node;
                model_node.setScAddr(el.id);
                model_node.setObjectState(SCgObjectState.FromMemory);
                elements[el.id] = model_node;
            } else if (el.el_type & sc_type_arc_mask) {
                edges.push(el);
            }
        }

        // create edges
        var founded = true;
        while (edges.length > 0 && founded) {
            founded = false;
            for (idx in edges) {
                var obj = edges[idx];
                var beginId = obj.begin;
                var endId = obj.end;
                // try to get begin and end object for arc
                if (elements.hasOwnProperty(beginId) && elements.hasOwnProperty(endId)) {
                    var beginNode = elements[beginId];
                    var endNode = elements[endId];
                    founded = true;
                    edges.splice(idx, 1);
                    var model_edge = SCg.Creator.createEdge(beginNode, endNode, obj.el_type);
                    this.editor.scene.appendEdge(model_edge);
                    this.editor.scene.objects[obj.id] = model_edge;
                    model_edge.setScAddr(obj.id);
                    model_edge.setObjectState(SCgObjectState.FromMemory);
                    elements[obj.id] = model_edge;
                }
            }
        }

        if (edges.length > 0)
            alert("error");

        this.editor.render.update();
        this.editor.scene.layout();
    };

    this.destroy = function () {
        delete this.editor;
        return true;
    };

    this.getObjectsToTranslate = function () {
        return this.editor.scene.getScAddrs();
    };

    this.applyTranslation = function (namesMap) {
        for (let addr in namesMap) {
            const obj = this.editor.scene.getObjectByScAddr(addr);
            if (obj) {
                obj.text = namesMap[addr];
            }
        }
        this.editor.render.updateTexts();
    };


    this.eventStructUpdate = function () {
        self.scStructTranslator.updateFromSc.apply(self.scStructTranslator, arguments).then(null);
    };

    // delegate event handlers
    this.sandbox.eventDataAppend = $.proxy(this.receiveData, this);
    this.sandbox.eventGetObjectsToTranslate = $.proxy(this.getObjectsToTranslate, this);
    this.sandbox.eventApplyTranslation = $.proxy(this.applyTranslation, this);
    this.sandbox.eventStructUpdate = $.proxy(this.eventStructUpdate, this);

    this.sandbox.updateContent();
};


SCWeb.core.ComponentManager.appendComponentInitialize(SCgComponent);
