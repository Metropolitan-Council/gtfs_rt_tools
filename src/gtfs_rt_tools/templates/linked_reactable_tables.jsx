const LinkedReactableTables = ({ data1, data2, title1 = "Feed 1", title2 = "Feed 2" }) => {
  const [sortColumn, setSortColumn] = useState(null);
  const [sortDirection, setSortDirection] = useState('asc');
  const [frozenColumns, setFrozenColumns] = useState([]);
  const [columnInput, setColumnInput] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [pageSize, setPageSize] = useState(50);
  const [currentPage, setCurrentPage] = useState(1);
  
  const table1Ref = useRef(null);
  const table2Ref = useRef(null);
  
  // Parse the HTML tables into structured data
  const parseTableData = (htmlString) => {
    const parser = new DOMParser();
    const doc = parser.parseFromString(htmlString, 'text/html');
    const table = doc.querySelector('table');
    
    if (!table) return { columns: [], data: [] };
    
    // Get columns from header
    const columns = Array.from(table.querySelectorAll('thead th'))
      .map(th => th.textContent.trim());
    
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
  
  const table1Data = parseTableData(data1);
  const table2Data = parseTableData(data2);
  
  // Sync horizontal scrolling between tables
/*   useEffect(() => {
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
  }, []); */
  
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
      .filter(col => col && table1Data.columns.includes(col));
    setFrozenColumns(newFrozenColumns);
  };
  
  const sortData = (data) => {
    if (!sortColumn) return data;
    
    return [...data].sort((a, b) => {
      const aVal = a[sortColumn];
      const bVal = b[sortColumn];
      
      // Try numeric comparison first
      const aNum = Number(aVal);
      const bNum = Number(bVal);
      
      if (!isNaN(aNum) && !isNaN(bNum)) {
        return sortDirection === 'asc' ? aNum - bNum : bNum - aNum;
      }
      
      // Fall back to string comparison
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
            disabled={currentPage === 1}
            className="px-3 py-1 rounded border hover:bg-gray-100 disabled:opacity-50"
          >
            Previous
          </button>
          <span className="text-sm text-gray-700">
            Page {currentPage} of {totalPages}
          </span>
          <button
            onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
            disabled={currentPage === totalPages}
            className="px-3 py-1 rounded border hover:bg-gray-100 disabled:opacity-50"
          >
            Next
          </button>
        </div>
      </div>
    );
  };
  
  const renderTable = (tableData, ref) => {
    const { columns, data } = tableData;
    const filteredData = filterData(data);
    const sortedData = sortData(filteredData);
    const paginatedData = paginateData(sortedData);
    
    return (
      <div className="bg-white rounded-lg shadow">
        <div 
          ref={ref}
          className="overflow-auto max-h-[600px]"
        >
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                {columns.map((column) => (
                  <th
                    key={column}
                    onClick={() => handleSort(column)}
                    className={`
                      px-6 py-3 text-left text-xs font-medium text-gray-500
                      cursor-pointer select-none
                      ${sortColumn === column ? 'bg-gray-100' : ''}
                      ${frozenColumns.includes(column) ? 'sticky left-0 z-10 bg-white' : ''}
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
              {paginatedData.map((row, rowIndex) => (
                <tr key={rowIndex} className="hover:bg-gray-50">
                  {columns.map((column) => (
                    <td
                      key={column}
                      className={`
                        px-6 py-4 whitespace-nowrap text-sm text-gray-900
                        ${frozenColumns.includes(column) ? 'sticky left-0 z-10 bg-white' : ''}
                        ${frozenColumns.includes(column) && row !== paginatedData[0] ? 'border-t border-gray-200' : ''}
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
        {renderPagination(filteredData.length)}
      </div>
    );
  };

  return (
    <div className="space-y-4 p-4">
      <div className="bg-white p-4 rounded-lg shadow space-y-4">
        <div className="flex gap-4">
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
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <h2 className="text-lg font-semibold mb-2">{title1}</h2>
          {renderTable(table1Data, table1Ref)}
        </div>

        <div>
          <h2 className="text-lg font-semibold mb-2">{title2}</h2>
          {renderTable(table2Data, table2Ref)}
        </div>
      </div>
    </div>
  );
};