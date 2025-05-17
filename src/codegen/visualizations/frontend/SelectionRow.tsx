import React, { useState, useEffect } from 'react';

interface Method {
  name: string;
  id: string;
}

interface RelatedElement {
  name: string;
  id: string;
  type: string;
}

interface SelectedElement {
  id: string;
  name: string;
  type: string;
  methods: Method[];
  related_elements: RelatedElement[];
}

interface SelectionRowProps {
  selectedElement: SelectedElement | null;
  onMethodSelect: (method: Method) => void;
  onRelatedElementSelect: (element: RelatedElement) => void;
}

/**
 * SelectionRow component displays information about the currently selected element
 * and allows interaction with its methods and related elements.
 */
const SelectionRow: React.FC<SelectionRowProps> = ({
  selectedElement,
  onMethodSelect,
  onRelatedElementSelect,
}) => {
  const [activeTab, setActiveTab] = useState<'methods' | 'related'>('methods');

  if (!selectedElement) {
    return (
      <div className="selection-row selection-row--empty">
        <div className="selection-row__placeholder">
          Select a Symbol, File, Function, or Class to view details
        </div>
      </div>
    );
  }

  const { name, type, methods, related_elements } = selectedElement;

  return (
    <div className="selection-row">
      <div className="selection-row__header">
        <div className="selection-row__element-info">
          <span className="selection-row__element-type">{type}</span>
          <h3 className="selection-row__element-name">{name}</h3>
        </div>
        <div className="selection-row__tabs">
          <button
            className={`selection-row__tab ${activeTab === 'methods' ? 'selection-row__tab--active' : ''}`}
            onClick={() => setActiveTab('methods')}
          >
            Methods ({methods?.length || 0})
          </button>
          <button
            className={`selection-row__tab ${activeTab === 'related' ? 'selection-row__tab--active' : ''}`}
            onClick={() => setActiveTab('related')}
          >
            Related Elements ({related_elements?.length || 0})
          </button>
        </div>
      </div>
      <div className="selection-row__content">
        {activeTab === 'methods' ? (
          <div className="selection-row__methods">
            {methods && methods.length > 0 ? (
              <ul className="selection-row__list">
                {methods.map((method) => (
                  <li key={method.id} className="selection-row__list-item">
                    <button
                      className="selection-row__list-button"
                      onClick={() => onMethodSelect(method)}
                    >
                      {method.name}
                    </button>
                  </li>
                ))}
              </ul>
            ) : (
              <div className="selection-row__empty-message">No methods available</div>
            )}
          </div>
        ) : (
          <div className="selection-row__related">
            {related_elements && related_elements.length > 0 ? (
              <ul className="selection-row__list">
                {related_elements.map((element) => (
                  <li key={element.id} className="selection-row__list-item">
                    <button
                      className="selection-row__list-button"
                      onClick={() => onRelatedElementSelect(element)}
                    >
                      <span className="selection-row__element-type-badge">{element.type}</span>
                      {element.name}
                    </button>
                  </li>
                ))}
              </ul>
            ) : (
              <div className="selection-row__empty-message">No related elements available</div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default SelectionRow;

