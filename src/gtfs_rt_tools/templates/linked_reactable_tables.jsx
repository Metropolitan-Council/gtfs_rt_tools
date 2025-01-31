const LinkedReactableTables = ({ data1, data2, title1 = "Feed 1", title2 = "Feed 2" }) => {
  const [sortColumn, setSortColumn] = useState(null);
  const [sortDirection, setSortDirection] = useState('asc');
  const [frozenColumns, setFrozenColumns] = useState([]);
  const [columnInput, setColumnInput] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [filterExpression, setFilterExpression] = useState('');
  const [pageSize, setPageSize] = useState(50);
  const [currentPage, setCurrentPage] = useState(1);
  const [showFilterHelp, setShowFilterHelp] = useState(false);
  const [tableData1, setTableData1] = useState(null);
  const [tableData2, setTableData2] = useState(null);
  const [loading, setLoading] = useState(false);
  
  const table1Ref = useRef(null);
  const table2Ref = useRef(null);
  const columnWidthsRef = useRef({});
  const originalColumnOrderRef = useRef(null);
  
  // Parse the HTML tables into structured data
  const parseTableData = (htmlString) => {
    const parser = new DOMParser();
    const doc = parser.parseFromString(htmlString, 'text/html');
    const table = doc.querySelector('table');
    
    if (!table) return { columns: [], data: [] };
    
    // Get columns from header
    const columns = Array.from(table.querySelectorAll('thead th'))
      .map(th => th.textContent.trim());
    
    // Store original column order if not already stored
    if (!originalColumnOrderRef.current) {
      originalColumnOrderRef.current = [...columns];
    }
    
    // Get data from rows
    const data = Array.from(table.querySelectorAll('tbody tr'))
      .map(row => {
        const rowData = {};
        Array.from(row.querySelectorAll('td')).forEach((cell, index) => {
          rowData[columns[index]] = cell.textContent.trim();
        });
        return rowData;
      });
      
    return { columns, data };
  };
  
  useEffect(() => {
    const parsedData1 = parseTableData(data1);
    const parsedData2 = parseTableData(data2);
    setTableData1(parsedData1);
    setTableData2(parsedData2);
  }, [data1, data2]);

  // Function to apply filter
  const applyFilter = async () => {
    setLoading(true);
    try {
      const response = await fetch('/filter', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          filter_expr: filterExpression,
          page: currentPage,
        }),
      });

      if (!response.ok) {
        throw new Error('Filter request failed');
      }

      const result = await response.json();
      
      if (result.error) {
        throw new Error(result.error);
      }

      // Update the tables with filtered data
      setTableData1(parseTableData(result.csv1));
      setTableData2(parseTableData(result.csv2));
      
      // Update pagination info if provided
      if (result.current_page) {
        setCurrentPage(result.current_page);
      }
    } catch (error) {
      console.error('Filter error:', error);
      alert(error.message);
    } finally {
      setLoading(false);
    }
  };

  // Effect to reapply filter when page changes
  useEffect(() => {
    if (filterExpression) {
      applyFilter();
    }
  }, [currentPage]);

  // Function to get ordered columns based on frozen state
  const getOrderedColumns = (columns) => {
    if (frozenColumns.length === 0) {
      // If no frozen columns, use original order
      return [...columns];
    }

    // Get non-frozen columns in their original order
    const nonFrozenColumns = originalColumnOrderRef.current.filter(
      col => !frozenColumns.includes(col)
    );

    // Return frozen columns first, followed by non-frozen columns
    return [...frozenColumns, ...nonFrozenColumns];
  };
  
  // Effect to measure column widths after render
  useEffect(() => {
    const table1Element = table1Ref.current;
    const table2Element = table2Ref.current;
    
    if (!table1Element || !table2Element) return;
    
    const newWidths = {};
    
    // Function to measure column widths from a table
    const measureTable = (tableElement) => {
      const headerCells = tableElement.querySelectorAll('thead th');
      const bodyCells = tableElement.querySelectorAll('tbody tr:first-child td');
      
      headerCells.forEach((cell, index) => {
        const columnName = cell.textContent.trim().split('↑')[0].split('↓')[0].trim();
        const headerWidth = cell.offsetWidth;
        const bodyWidth = bodyCells[index]?.offsetWidth || 0;
        const maxWidth = Math.max(headerWidth, bodyWidth);
        
        newWidths[columnName] = Math.max(newWidths[columnName] || 0, maxWidth);
      });
    };
    
    measureTable(table1Element);
    measureTable(table2Element);
    
    columnWidthsRef.current = newWidths;
  }, [data1, data2, frozenColumns]);

  // Sync horizontal scrolling between tables
  useEffect(() => {
    const table1Element = table1Ref.current;
    const table2Element = table2Ref.current;
    
    if (!table1Element || !table2Element) return;
    
    const syncScroll = (source, target) => {
      target.scrollLeft = source.scrollLeft;
    };
    
    const handleTable1Scroll = () => syncScroll(table1Element, table2Element);
    const handleTable2Scroll = () => syncScroll(table2Element, table1Element);
    
    table1Element.addEventListener('scroll', handleTable1Scroll);
    table2Element.addEventListener('scroll', handleTable2Scroll);
    
    return () => {
      table1Element.removeEventListener('scroll', handleTable1Scroll);
      table2Element.removeEventListener('scroll', handleTable2Scroll);
    };
  }, []);
  
  const handleSort = (column) => {
    if (sortColumn === column) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortColumn(column);
      setSortDirection('asc');
    }
  };
  
  const handleFreezeColumns = () => {
    const newFrozenColumns = columnInput
      .split(',')
      .map(col => col.trim())
      .filter(col => col && originalColumnOrderRef.current.includes(col));
    setFrozenColumns(newFrozenColumns);
  };

  const getFrozenColumnStyle = (column, isTable2 = false) => {
    if (!frozenColumns.includes(column)) return {};
    
    const columnIndex = frozenColumns.indexOf(column);
    let leftPosition = 0;
    
    for (let i = 0; i < columnIndex; i++) {
      const prevColumn = frozenColumns[i];
      leftPosition += columnWidthsRef.current[prevColumn] || 0;
    }
    
    return {
      position: 'sticky',
      left: `${leftPosition}px`,
      zIndex: 10,
      backgroundColor: 'white',
      boxShadow: '2px 0 4px rgba(0,0,0,0.1)',
      minWidth: `${columnWidthsRef.current[column]}px`
    };
  };
  
  const sortData = (data) => {
    if (!sortColumn) return data;
    
    return [...data].sort((a, b) => {
      const aVal = a[sortColumn];
      const bVal = b[sortColumn];
      
      const aNum = Number(aVal);
      const bNum = Number(bVal);
      
      if (!isNaN(aNum) && !isNaN(bNum)) {
        return sortDirection === 'asc' ? aNum - bNum : bNum - aNum;
      }
      
      return sortDirection === 'asc' 
        ? String(aVal).localeCompare(String(bVal))
        : String(bVal).localeCompare(String(aVal));
    });
  };
  
  const filterData = (data) => {
    if (!searchTerm) return data;
    
    const searchLower = searchTerm.toLowerCase();
    return data.filter(row => 
      Object.values(row).some(value => 
        String(value).toLowerCase().includes(searchLower)
      )
    );
  };

  const paginateData = (data) => {
    const startIndex = (currentPage - 1) * pageSize;
    return data.slice(startIndex, startIndex + pageSize);
  };

  const renderPagination = (totalRows) => {
    const totalPages = Math.ceil(totalRows / pageSize);
    
    return (
      <div className="flex items-center justify-between px-2 py-3 bg-white border-t">
        <div className="flex items-center">
          <select
            value={pageSize}
            onChange={(e) => {
              setPageSize(Number(e.target.value));
              setCurrentPage(1);
            }}
            className="mr-4 rounded border-gray-300"
          >
            {[25, 50, 100, 250, 500].map(size => (
              <option key={size} value={size}>{size} rows</option>
            ))}
          </select>
          <span className="text-sm text-gray-700">
            Showing {Math.min((currentPage - 1) * pageSize + 1, totalRows)} to {Math.min(currentPage * pageSize, totalRows)} of {totalRows} entries
          </span>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
            disabled={currentPage === 1 || loading}
            className="px-3 py-1 rounded border hover:bg-gray-100 disabled:opacity-50"
          >
            Previous
          </button>
          <span className="text-sm text-gray-700">
            Page {currentPage} of {totalPages}
          </span>
          <button
            onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
            disabled={currentPage === totalPages || loading}
            className="px-3 py-1 rounded border hover:bg-gray-100 disabled:opacity-50"
          >
            Next
          </button>
        </div>
      </div>
    );
  };
  
  const renderTable = (tableData, ref, isTable2 = false) => {
    if (!tableData) return null;
    
    const { columns, data } = tableData;
    const orderedColumns = getOrderedColumns(columns);
    
    return (
      <div className="bg-white rounded-lg shadow">
        <div 
          ref={ref}
          className="overflow-auto max-h-[600px]"
        >
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                {orderedColumns.map((column) => (
                  <th
                    key={column}
                    onClick={() => handleSort(column)}
                    style={getFrozenColumnStyle(column, isTable2)}
                    className={`
                      px-6 py-3 text-left text-xs font-medium text-gray-500
                      cursor-pointer select-none
                      ${sortColumn === column ? 'bg-gray-100' : ''}
                    `}
                  >
                    <div className="flex items-center space-x-1">
                      <span>{column}</span>
                      {sortColumn === column && (
                        <span className="ml-2">
                          {sortDirection === 'asc' ? '↑' : '↓'}
                        </span>
                      )}
                    </div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {data.map((row, rowIndex) => (
                <tr key={rowIndex} className="hover:bg-gray-50">
                  {orderedColumns.map((column) => (
                    <td
                      key={column}
                      style={getFrozenColumnStyle(column, isTable2)}
                      className={`
                        px-6 py-4 whitespace-nowrap text-sm text-gray-900
                        ${rowIndex !== 0 ? 'border-t border-gray-200' : ''}
                      `}
                    >
                      {row[column]}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {renderPagination(data.length)}
      </div>
    );
  };

const filterHelpText = `
    Filter Expression Examples:
    - Single condition: route_id = 10
    - Multiple AND conditions: route_id = 10 AND trip_id = 123
    - OR conditions: route_id = 10 OR route_id = 11
    - Complex grouping: (route_id = 10 OR route_id = 11) AND trip_id = 123
    - Numeric comparisons: departure_delay > 300
  `;

  return (
    <div className="space-y-4 p-4">
      <div className="bg-white p-4 rounded-lg shadow space-y-4">
        {/* Search and Column Freeze Controls */}
        <div className="flex gap-4 mb-4">
          <input
            type="text"
            placeholder="Search all columns..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="flex-1 px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <div className="flex-1 flex gap-4">
            <input
              type="text"
              placeholder="Enter column names to freeze (comma-separated)"
              value={columnInput}
              onChange={(e) => setColumnInput(e.target.value)}
              className="flex-1 px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <button
              onClick={handleFreezeColumns}
              className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              Freeze Columns
            </button>
          </div>
        </div>

        {/* Filter Controls */}
        <div className="flex gap-4 items-start">
          <div className="flex-1 space-y-2">
            <div className="flex gap-4">
              <input
                type="text"
                placeholder="Enter filter expression..."
                value={filterExpression}
                onChange={(e) => setFilterExpression(e.target.value)}
                className="flex-1 px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <button
                onClick={applyFilter}
                disabled={loading}
                className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:hover:bg-blue-500"
              >
                {loading ? 'Filtering...' : 'Apply Filter'}
              </button>
            </div>
            <button
              onClick={() => setShowFilterHelp(!showFilterHelp)}
              className="text-sm text-blue-600 hover:text-blue-800"
            >
              {showFilterHelp ? 'Hide filter help' : 'Show filter help'}
            </button>
            {showFilterHelp && (
              <div className="mt-2 p-3 bg-gray-50 rounded-lg text-sm text-gray-600 whitespace-pre-line">
                {filterHelpText}
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <h2 className="text-lg font-semibold mb-2">{title1}</h2>
          {renderTable(tableData1, table1Ref, false)}
        </div>
        <div>
          <h2 className="text-lg font-semibold mb-2">{title2}</h2>
          {renderTable(tableData2, table2Ref, true)}
        </div>
      </div>
    </div>
  );
};
