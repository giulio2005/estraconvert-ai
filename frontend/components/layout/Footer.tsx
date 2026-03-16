'use client';

import Link from 'next/link';
import { FileSpreadsheet } from 'lucide-react';

export default function Footer() {
  return (
    <footer className="bg-gray-900 text-white py-12">
      <div className="max-w-7xl mx-auto px-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          <div>
            <div className="flex items-center space-x-3 mb-4">
              <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
                <FileSpreadsheet className="text-white" size={16} />
              </div>
              <span className="text-lg font-semibold">EstraConvert</span>
            </div>
            <p className="text-gray-400">Converti i tuoi estratti conto in CSV facilmente e velocemente.</p>
          </div>
          <div>
            <h5 className="font-semibold mb-4">Prodotto</h5>
            <ul className="space-y-2 text-gray-400">
              <li><Link href="/convert" className="hover:text-white transition-colors">Come funziona</Link></li>
              <li><span className="hover:text-white transition-colors cursor-pointer">Formati supportati</span></li>
              <li><span className="hover:text-white transition-colors cursor-pointer">API</span></li>
            </ul>
          </div>
          <div>
            <h5 className="font-semibold mb-4">Supporto</h5>
            <ul className="space-y-2 text-gray-400">
              <li><span className="hover:text-white transition-colors cursor-pointer">Centro assistenza</span></li>
              <li><span className="hover:text-white transition-colors cursor-pointer">Contatti</span></li>
              <li><span className="hover:text-white transition-colors cursor-pointer">FAQ</span></li>
            </ul>
          </div>
          <div>
            <h5 className="font-semibold mb-4">Legale</h5>
            <ul className="space-y-2 text-gray-400">
              <li><span className="hover:text-white transition-colors cursor-pointer">Privacy Policy</span></li>
              <li><span className="hover:text-white transition-colors cursor-pointer">Termini di servizio</span></li>
              <li><span className="hover:text-white transition-colors cursor-pointer">Cookie Policy</span></li>
            </ul>
          </div>
        </div>
        <div className="border-t border-gray-800 mt-8 pt-8 text-center text-gray-400">
          <p>&copy; 2024 EstraConvert. Tutti i diritti riservati.</p>
        </div>
      </div>
    </footer>
  );
}
