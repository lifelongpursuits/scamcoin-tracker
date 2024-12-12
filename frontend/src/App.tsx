import React, { useState, useEffect, useCallback } from 'react';
import {
  Container,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  List,
  ListItem,
  ListItemText,
  Box,
  Alert,
  CircularProgress,
  Avatar,
  TextField,
  Popper,
  ClickAwayListener
} from '@mui/material';
import axios, { AxiosError } from 'axios';
import { debounce } from 'lodash';

// Use environment variable for API base URL
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000/api';
console.log('API Base URL:', API_BASE_URL);

interface Cryptocurrency {
  id: number;
  name: string;
  symbol: string;
  price: number;
  percent_change_24h: number;
  percent_change_7d: number;
  market_cap: number;
  is_default: boolean;
  logo: string;
}

interface SearchResult {
  symbol: string;
  name: string;
}

const App: React.FC = () => {
  const [cryptocurrencies, setCryptocurrencies] = useState<Cryptocurrency[]>([]);
  const [isSearchDialogOpen, setIsSearchDialogOpen] = useState<boolean>(false);
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [error, setError] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);

  const fetchCryptocurrencies = async (): Promise<void> => {
    setIsLoading(true);
    setError('');
    try {
      const fullUrl = `${API_BASE_URL}/cryptocurrencies`;
      console.log('Attempting to fetch cryptocurrencies from FULL URL:', fullUrl);
      
      const response = await axios({
        method: 'get',
        url: fullUrl,
        timeout: 10000,
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json'
        }
      });
      
      console.log('Fetch successful, received data:', response.data);
      
      // Sort cryptocurrencies to ensure default coins are first
      const sortedCryptos = response.data.sort((a: Cryptocurrency, b: Cryptocurrency) => 
        a.is_default === b.is_default ? 0 : a.is_default ? -1 : 1
      );
      
      setCryptocurrencies(sortedCryptos);
      setIsLoading(false);
    } catch (error) {
      setIsLoading(false);
      console.error('Full error object:', error);
      
      if (axios.isAxiosError(error)) {
        const axiosError = error as AxiosError;
        if (axiosError.response) {
          console.error('Response data:', axiosError.response.data);
          console.error('Response status:', axiosError.response.status);
          
          // If we receive fallback data
          if (axiosError.response.data && Array.isArray(axiosError.response.data)) {
            setCryptocurrencies(axiosError.response.data);
            setError('Unable to fetch live cryptocurrency data. Showing default coins.');
          } else {
            setError(`Server Error: ${JSON.stringify(axiosError.response.data)}`);
          }
        } else if (axiosError.request) {
          console.error('No response received:', axiosError.request);
          setError('No response from server. Check your network connection.');
        } else {
          console.error('Error setting up request:', axiosError.message);
          setError('Error setting up the request. Check your network connection.');
        }
      } else {
        console.error('Unexpected error:', error);
        setError('An unexpected error occurred');
      }
    }
  };

  useEffect(() => {
    const checkServerConnectivity = async () => {
      try {
        console.log('Checking server connectivity...');
        const pingResponse = await axios({
          method: 'get',
          url: '/api/ping',
          timeout: 5000
        });
        
        console.log('Server connectivity check SUCCESS:', pingResponse.data);
        
        // Validate the response structure
        if (pingResponse.data && pingResponse.data.status === 'ok') {
          return true;
        } else {
          console.error('Invalid ping response:', pingResponse.data);
          setError('Unexpected server response');
          return false;
        }
      } catch (error) {
        console.error('Server connectivity check FAILED:', error);
        
        if (axios.isAxiosError(error)) {
          const axiosError = error as AxiosError;
          console.error('Detailed axios error:', {
            message: axiosError.message,
            code: axiosError.code,
            config: {
              url: axiosError.config?.url,
              method: axiosError.config?.method,
              timeout: axiosError.config?.timeout
            }
          });

          // More specific error messages
          if (axiosError.code === 'ECONNABORTED') {
            setError('Server connection timed out. Is the backend running?');
          } else if (axiosError.message.includes('Network Error')) {
            setError('Network error. Please check your server connection.');
          } else {
            setError(`Unable to connect to the server: ${axiosError.message}`);
          }
        } else {
          setError('An unexpected error occurred during server connectivity check.');
        }
        
        return false;
      }
    };

    const initializeApp = async () => {
      const isConnected = await checkServerConnectivity();
      if (isConnected) {
        await fetchCryptocurrencies();
      }
    };

    initializeApp();
    const interval = setInterval(fetchCryptocurrencies, 60000);
    return () => clearInterval(interval);
  }, []);

  const searchCryptocurrencies = async (query: string): Promise<void> => {
    if (query.length < 2) {
      setSearchResults([]);
      return;
    }

    try {
      const response = await axios({
        method: 'get',
        url: `${API_BASE_URL}/cryptocurrency/search/${encodeURIComponent(query)}`,
        timeout: 5000,
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json'
        }
      });

      // Validate and transform search results
      const validResults = response.data
        .filter((result: SearchResult) => 
          result.symbol.toLowerCase().includes(query.toLowerCase()) || 
          result.name.toLowerCase().includes(query.toLowerCase())
        )
        .slice(0, 10);  // Limit to top 10 results

      setSearchResults(validResults);
    } catch (error) {
      console.error('Search error:', error);
      if (axios.isAxiosError(error)) {
        console.error('Response data:', error.response?.data);
        console.error('Response status:', error.response?.status);
        setError(`Search failed: ${error.response?.data?.error || 'Unknown error'}`);
      } else {
        setError('Failed to perform search. Please try again.');
      }
      setSearchResults([]);
    }
  };

  const debouncedSearch = useCallback(
    debounce((query: string) => {
      searchCryptocurrencies(query);
    }, 300),
    []
  );

  const handleSearchChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const query = event.target.value;
    setSearchTerm(query);
    setAnchorEl(event.currentTarget);
    debouncedSearch(query);
  };

  const handleAddCrypto = async (symbol: string): Promise<void> => {
    try {
      console.log('Attempting to add cryptocurrency with symbol:', symbol);
      const response = await axios.get(`${API_BASE_URL}/cryptocurrency/add/${symbol}`);
      console.log('Add successful, received data:', response.data);
      
      // Fetch updated cryptocurrencies after adding
      await fetchCryptocurrencies();
      
      // Close search dialog
      setIsSearchDialogOpen(false);
      
      // Clear search results and term
      setSearchResults([]);
      setSearchTerm('');
      
      // Show success message
      setError('');
    } catch (error: unknown) {
      if (axios.isAxiosError(error)) {
        const errorMessage = error.response?.data?.error || 'Failed to add cryptocurrency';
        setError(errorMessage);
        console.error('Add Crypto Error:', errorMessage);
      } else {
        setError('An unexpected error occurred');
        console.error('Unexpected error:', error);
      }
    }
  };

  const handleSelectSearchResult = (result: SearchResult) => {
    handleAddCrypto(result.symbol);
    setSearchTerm('');
    setSearchResults([]);
    setAnchorEl(null);
  };

  return (
    <Container maxWidth="lg" sx={{ 
      mt: 4, 
      mb: 4, 
      backgroundColor: '#121212', 
      minHeight: '100vh', 
      color: 'white' 
    }}>
      <Typography variant="h4" gutterBottom sx={{ color: 'white', textAlign: 'center', pt: 2 }}>
        Cryptocurrency Price Tracker
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Box sx={{ 
        mb: 2, 
        display: 'flex', 
        gap: 2, 
        justifyContent: 'center', 
        alignItems: 'center' 
      }}>
        <Button
          variant="contained"
          onClick={() => setIsSearchDialogOpen(true)}
          sx={{ 
            backgroundColor: '#1976d2', 
            '&:hover': { 
              backgroundColor: '#1565c0' 
            } 
          }}
        >
          Add Coin
        </Button>
      </Box>

      {isLoading ? (
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
          <CircularProgress />
        </Box>
      ) : (
        <TableContainer component={Paper} sx={{ backgroundColor: '#1e1e1e' }}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell sx={{ color: 'white' }}>Name</TableCell>
                <TableCell sx={{ color: 'white' }}>Symbol</TableCell>
                <TableCell align="right" sx={{ color: 'white' }}>Price (USD)</TableCell>
                <TableCell align="right" sx={{ color: 'white' }}>24h Change (%)</TableCell>
                <TableCell align="right" sx={{ color: 'white' }}>7d Change (%)</TableCell>
                <TableCell align="right" sx={{ color: 'white' }}>Market Cap</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {cryptocurrencies.map((crypto) => (
                <TableRow key={crypto.id}>
                  <TableCell sx={{ display: 'flex', alignItems: 'center', color: 'white' }}>
                    <Avatar 
                      src={crypto.logo} 
                      alt={`${crypto.name} logo`} 
                      sx={{ width: 30, height: 30, mr: 2 }} 
                    />
                    {crypto.name}
                  </TableCell>
                  <TableCell sx={{ color: 'white' }}>{crypto.symbol}</TableCell>
                  <TableCell align="right" sx={{ color: 'white' }}>${crypto.price.toFixed(2)}</TableCell>
                  <TableCell
                    align="right"
                    sx={{
                      color: crypto.percent_change_24h >= 0 ? 'success.main' : 'error.main',
                    }}
                  >
                    {crypto.percent_change_24h.toFixed(2)}%
                  </TableCell>
                  <TableCell
                    align="right"
                    sx={{
                      color: crypto.percent_change_7d >= 0 ? 'success.main' : 'error.main',
                    }}
                  >
                    {crypto.percent_change_7d.toFixed(2)}%
                  </TableCell>
                  <TableCell align="right" sx={{ color: 'white' }}>
                    ${(crypto.market_cap / 1_000_000).toFixed(2)}M
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      <Dialog
        open={isSearchDialogOpen}
        onClose={() => setIsSearchDialogOpen(false)}
        maxWidth="sm"
        fullWidth
        sx={{ 
          '& .MuiDialog-paper': { 
            backgroundColor: '#1e1e1e', 
            color: 'white' 
          } 
        }}
      >
        <DialogTitle sx={{ color: 'white' }}>Add Cryptocurrency</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Search Cryptocurrencies"
            fullWidth
            value={searchTerm}
            onChange={handleSearchChange}
            InputLabelProps={{
              style: { color: 'white' }
            }}
            sx={{
              '& .MuiOutlinedInput-root': {
                '& fieldset': {
                  borderColor: 'white',
                },
                '&:hover fieldset': {
                  borderColor: 'white',
                },
                '&.Mui-focused fieldset': {
                  borderColor: 'white',
                },
              },
              input: {
                color: 'white'
              }
            }}
          />
          <List>
            {searchResults.map((result) => (
              <ListItem
                key={result.symbol}
                onClick={() => handleAddCrypto(result.symbol)}
                sx={{ 
                  color: 'white', 
                  '&:hover': { 
                    backgroundColor: 'rgba(255,255,255,0.1)' 
                  } 
                }}
              >
                <ListItemText
                  primary={result.name}
                  secondary={result.symbol}
                  primaryTypographyProps={{ color: 'white' }}
                  secondaryTypographyProps={{ color: 'gray' }}
                />
              </ListItem>
            ))}
          </List>
        </DialogContent>
      </Dialog>

      {searchResults.length > 0 && (
        <Popper 
          open={Boolean(anchorEl)} 
          anchorEl={anchorEl} 
          placement="bottom-start" 
          style={{ width: anchorEl?.clientWidth }}
        >
          <ClickAwayListener onClickAway={() => setAnchorEl(null)}>
            <Paper>
              <List>
                {searchResults.map((result) => (
                  <ListItem 
                    key={result.symbol} 
                    button 
                    onClick={() => handleSelectSearchResult(result)}
                  >
                    <ListItemText 
                      primary={`${result.symbol} - ${result.name}`} 
                    />
                  </ListItem>
                ))}
              </List>
            </Paper>
          </ClickAwayListener>
        </Popper>
      )}
    </Container>
  );
};

export default App;
