import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from '@/components/ui/select';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ChevronRight, ChevronLeft } from 'lucide-react';
import { logout } from '@/lib/auth';
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
} from '@/components/ui/dialog';

interface SideBarProps {
    onConfigured?: () => void;
}

type ProviderModels = {
    [key: string]: string[];
};

const PROVIDER_MODELS: ProviderModels = {
    openai: ['gpt-3.5-turbo', 'gpt-4', 'gpt-4-0125-preview', 'gpt-4o-mini'],
    anthropic: [
        'claude-3-sonnet-20240229',
        'claude-3-haiku-20240307',
        'claude-3-opus-20240229',
    ],
};

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost/api';

export const SideBar = ({ onConfigured }: SideBarProps) => {
    const [isOpen, setIsOpen] = useState(false);
    const [selectedProvider, setSelectedProvider] = useState('');
    const [selectedModel, setSelectedModel] = useState('');
    const [apiKey, setApiKey] = useState('');
    const [isConfiguring, setIsConfiguring] = useState(false);
    const [dialogOpen, setDialogOpen] = useState(false);
    const [isConfigured, setIsConfigured] = useState(false);
    const [errorMessage, setErrorMessage] = useState('');
    const router = useRouter();

    useEffect(() => {
        fetchCurrentConfig();
    }, []);

    const fetchCurrentConfig = async () => {
        try {
            const response = await fetch(`${API_URL}/api/model-config`);
            if (response.ok) {
                const data = await response.json();
                setSelectedProvider(data.provider || '');
                setSelectedModel(data.model || '');
                setIsConfigured(!!data.provider && !!data.model);
                if (data.message) {
                    setErrorMessage(data.message);
                }
            } else {
                const errorData = await response.json();
                setErrorMessage(
                    errorData.detail || 'Failed to fetch configuration'
                );
            }
        } catch (error) {
            console.error('Error fetching current config:', error);
            setErrorMessage('Failed to fetch configuration. Please try again.');
        }
    };

    const handleSaveConfig = async () => {
        setIsConfiguring(true);
        setErrorMessage('');
        try {
            const response = await fetch(`${API_URL}/api/configure-model`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    provider: selectedProvider,
                    model: selectedModel,
                    apiKey: apiKey,
                }),
            });

            if (response.ok) {
                console.log('Configuration saved successfully');
                setDialogOpen(false);
                setApiKey('');
                setIsConfigured(true);
                await fetchCurrentConfig();
                if (onConfigured) {
                    onConfigured();
                }
            } else {
                const errorData = await response.json();
                setErrorMessage(
                    errorData.detail || 'Failed to save configuration'
                );
            }
        } catch (error) {
            console.error('Error saving configuration:', error);
            setErrorMessage(
                'An error occurred while saving the configuration. Please try again.'
            );
        } finally {
            setIsConfiguring(false);
        }
    };

    const handleLogout = () => {
        logout();
        router.push('/login');
    };

    return (
        <div className="fixed top-0 right-0 h-full z-20">
            <Button
                className={`absolute top-4 ${
                    isOpen ? '-left-8' : 'right-0'
                } z-20`}
                size="sm"
                variant="outline"
                onClick={() => setIsOpen(!isOpen)}
            >
                {isOpen ? (
                    <ChevronRight className="h-4 w-4" />
                ) : (
                    <ChevronLeft className="h-4 w-4" />
                )}
            </Button>
            <div
                className={`h-full bg-white shadow-lg transition-all duration-300 ease-in-out overflow-hidden ${
                    isOpen ? 'w-64' : 'w-0'
                }`}
            >
                <div className="p-4 h-full overflow-y-auto flex flex-col justify-between">
                    <div>
                        <h2 className="text-lg font-semibold mb-4">
                            Model Configuration
                        </h2>
                        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
                            <DialogTrigger asChild>
                                <Button
                                    className="w-full mt-4"
                                    onClick={() => setDialogOpen(true)}
                                >
                                    Configure Model
                                </Button>
                            </DialogTrigger>
                            <DialogContent className="sm:max-w-[425px]">
                                <DialogHeader>
                                    <DialogTitle>
                                        Model Configuration
                                    </DialogTitle>
                                </DialogHeader>
                                <div className="grid gap-4 py-4">
                                    <div className="grid grid-cols-4 items-center gap-4">
                                        <label
                                            htmlFor="providerSelect"
                                            className="text-right"
                                        >
                                            Provider
                                        </label>
                                        <Select
                                            onValueChange={(value) => {
                                                setSelectedProvider(value);
                                                setSelectedModel(''); // Reset model when provider changes
                                            }}
                                            value={selectedProvider}
                                        >
                                            <SelectTrigger
                                                id="providerSelect"
                                                className="col-span-3"
                                            >
                                                <SelectValue placeholder="Select a provider" />
                                            </SelectTrigger>
                                            <SelectContent>
                                                {Object.keys(
                                                    PROVIDER_MODELS
                                                ).map((provider) => (
                                                    <SelectItem
                                                        key={provider}
                                                        value={provider}
                                                    >
                                                        {provider}
                                                    </SelectItem>
                                                ))}
                                            </SelectContent>
                                        </Select>
                                    </div>
                                    {selectedProvider && (
                                        <div className="grid grid-cols-4 items-center gap-4">
                                            <label
                                                htmlFor="modelSelect"
                                                className="text-right"
                                            >
                                                Model
                                            </label>
                                            <Select
                                                onValueChange={setSelectedModel}
                                                value={selectedModel}
                                            >
                                                <SelectTrigger
                                                    id="modelSelect"
                                                    className="col-span-3"
                                                >
                                                    <SelectValue placeholder="Select a model" />
                                                </SelectTrigger>
                                                <SelectContent>
                                                    {PROVIDER_MODELS[
                                                        selectedProvider
                                                    ] &&
                                                        PROVIDER_MODELS[
                                                            selectedProvider
                                                        ].map((model) => (
                                                            <SelectItem
                                                                key={model}
                                                                value={model}
                                                            >
                                                                {model}
                                                            </SelectItem>
                                                        ))}
                                                </SelectContent>
                                            </Select>
                                        </div>
                                    )}
                                    <div className="grid grid-cols-4 items-center gap-4">
                                        <label
                                            htmlFor="apiKey"
                                            className="text-right"
                                        >
                                            API Key
                                        </label>
                                        <Input
                                            id="apiKey"
                                            type="password"
                                            value={apiKey}
                                            onChange={(e) =>
                                                setApiKey(e.target.value)
                                            }
                                            className="col-span-3"
                                        />
                                    </div>
                                </div>
                                <Button
                                    onClick={handleSaveConfig}
                                    disabled={
                                        isConfiguring ||
                                        !selectedProvider ||
                                        !selectedModel ||
                                        !apiKey
                                    }
                                >
                                    {isConfiguring
                                        ? 'Saving...'
                                        : 'Save Configuration'}
                                </Button>
                                {errorMessage && (
                                    <p className="text-red-500 mt-2 text-sm">
                                        {errorMessage}
                                    </p>
                                )}
                            </DialogContent>
                        </Dialog>
                    </div>
                    <Button
                        onClick={handleLogout}
                        className="w-full bg-red-500 hover:bg-red-600 text-white"
                    >
                        Logout
                    </Button>
                </div>
            </div>
        </div>
    );
};
